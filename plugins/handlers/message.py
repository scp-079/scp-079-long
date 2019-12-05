# SCP-079-LONG - Control super long messages
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-LONG.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from telegram import Update
from telegram.ext import CallbackContext, Dispatcher, Filters, MessageHandler

from .. import glovar
from ..functions.channel import get_debug_text
from ..functions.etc import code, general_link, get_full_name, get_now, lang, thread, mention_id
from ..functions.file import save
from ..functions.filters import authorized_group, class_c, class_d, declared_message, exchange_channel, from_user
from ..functions.filters import hide_channel, is_class_d_user, is_declared_message, is_long_text, is_nm_text
from ..functions.filters import new_group, test_group
from ..functions.group import leave_group
from ..functions.ids import init_group_id, init_user_id
from ..functions.receive import receive_add_bad, receive_add_except, receive_clear_data, receive_config_commit
from ..functions.receive import receive_config_reply, receive_config_show, receive_declared_message
from ..functions.receive import receive_leave_approve, receive_refresh, receive_regex, receive_remove_bad
from ..functions.receive import receive_remove_except, receive_remove_score, receive_remove_watch, receive_rollback
from ..functions.receive import receive_text_data, receive_user_score, receive_watch_user
from ..functions.telegram import get_admins, send_message
from ..functions.tests import long_test
from ..functions.timers import backup_files, send_count
from ..functions.user import terminate_user

# Enable logging
logger = logging.getLogger(__name__)


def add_message_handlers(dispatcher: Dispatcher) -> bool:
    # Add message handlers
    try:
        # Check
        dispatcher.add_handler(MessageHandler(
            filters=(Filters.update.messages & Filters.group & ~Filters.status_update
                     & ~test_group & authorized_group
                     & from_user & ~class_c & ~class_d
                     & ~declared_message),
            callback=check
        ))
        # Check join
        dispatcher.add_handler(MessageHandler(
            filters=(Filters.group & ~test_group & Filters.status_update.new_chat_members
                     & ~test_group & ~new_group & authorized_group
                     & from_user & ~class_c & ~class_d
                     & ~declared_message),
            callback=check_join
        ))
        # Exchange emergency
        dispatcher.add_handler(MessageHandler(
            filters=(Filters.update.channel_post
                     & hide_channel),
            callback=exchange_emergency
        ))
        # Init group
        dispatcher.add_handler(MessageHandler(
            filters=(Filters.group & (Filters.status_update.new_chat_members | Filters.status_update.chat_created)
                     & ~test_group & new_group
                     & from_user),
            callback=init_group
        ))
        # Process data
        dispatcher.add_handler(MessageHandler(
            filters=(Filters.update.channel_post
                     & exchange_channel),
            callback=process_data
        ))
        # Test
        dispatcher.add_handler(MessageHandler(
            filters=(Filters.update.messages & Filters.group & ~Filters.status_update
                     & test_group
                     & from_user),
            callback=test
        ))

        return True
    except Exception as e:
        logger.warning(f"Add message handlers error: {e}", exc_info=True)

    return False


def check(update: Update, context: CallbackContext) -> bool:
    # Check the messages sent from groups
    glovar.locks["message"].acquire()
    try:
        client = context.bot
        message = update.effective_message

        # Check declare status
        if is_declared_message(message):
            return True

        # Super long message
        detection = is_long_text(message)
        if detection:
            return terminate_user(client, message, detection)

        return True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def check_join(update: Update, context: CallbackContext) -> bool:
    # Check new joined user
    glovar.locks["message"].acquire()
    try:
        _ = context.bot
        message = update.effective_message

        # Basic data
        gid = message.chat.id
        now = int(message.date.strftime("%s")) or get_now()

        for new in message.new_chat_members:
            # Basic data
            uid = new.id

            # Check if the user is Class D personnel
            if is_class_d_user(new):
                return True

            # Work with NOSPAM
            if glovar.nospam_id in glovar.admin_ids[gid]:
                # Check name
                name = get_full_name(new, True)
                if name and is_nm_text(name):
                    return True

            # Check declare status
            if is_declared_message(message):
                return True

            # Init the user's status
            if not init_user_id(uid):
                continue

            # Update user's join status
            glovar.user_ids[uid]["join"][gid] = now
            save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def exchange_emergency(update: Update, context: CallbackContext) -> bool:
    # Sent emergency channel transfer request
    try:
        client = context.bot
        message = update.effective_message

        # Read basic information
        data = receive_text_data(message)
        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        if "EMERGENCY" not in receivers:
            return True

        if action != "backup":
            return True

        if action_type != "hide":
            return True

        if data is True:
            glovar.should_hide = data
        elif data is False and sender == "MANAGE":
            glovar.should_hide = data

        project_text = general_link(glovar.project_name, glovar.project_link)
        hide_text = (lambda x: lang("enabled") if x else "disabled")(glovar.should_hide)
        text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n"
                f"{lang('emergency_channel')}{lang('colon')}{code(hide_text)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


def init_group(update: Update, context: CallbackContext) -> bool:
    # Initiate new groups
    try:
        client = context.bot
        message = update.effective_message

        # Basic data
        gid = message.chat.id
        inviter = message.from_user.id

        # Text prefix
        text = get_debug_text(client, message.chat)

        # Check permission
        if inviter.id == glovar.user_id:
            # Remove the left status
            if gid in glovar.left_group_ids:
                glovar.left_group_ids.discard(gid)

            # Update group's admin list
            if not init_group_id(gid):
                return True

            admin_members = get_admins(client, gid)

            if admin_members:
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                         if not admin.user.is_bot}
                save("admin_ids")
                text += f"{lang('status')}{lang('colon')}{code(lang('status_joined'))}\n"
            else:
                thread(leave_group, (client, gid))
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_admin'))}\n")
        else:
            if gid in glovar.left_group_ids:
                return leave_group(client, gid)

            leave_group(client, gid)

            text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('reason_unauthorized'))}\n")

        # Add inviter info
        if message.from_user.username:
            text += f"{lang('inviter')}{lang('colon')}{mention_id(inviter.id)}\n"
        else:
            text += f"{lang('inviter')}{lang('colon')}{code(inviter.id)}\n"

        # Send debug message
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)

    return False


def process_data(update: Update, context: CallbackContext) -> bool:
    # Process the data in exchange channel
    glovar.locks["receive"].acquire()
    try:
        client = context.bot
        message = update.effective_message

        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        # This will look awkward,
        # seems like it can be simplified,
        # but this is to ensure that the permissions are clear,
        # so it is intentionally written like this
        if glovar.sender in receivers:

            if sender == "CAPTCHA":

                if action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CLEAN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CONFIG":

                if action == "config":
                    if action_type == "commit":
                        receive_config_commit(data)
                    elif action_type == "reply":
                        receive_config_reply(client, data)

            elif sender == "LANG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "MANAGE":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "except":
                        receive_add_except(data)

                elif action == "backup":
                    if action_type == "now":
                        thread(backup_files, (client,))
                    elif action_type == "rollback":
                        receive_rollback(client, message, data)

                elif action == "clear":
                    receive_clear_data(client, action_type, data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, data)

                elif action == "leave":
                    if action_type == "approve":
                        receive_leave_approve(client, data)

                elif action == "remove":
                    if action_type == "bad":
                        receive_remove_bad(data)
                    elif action_type == "except":
                        receive_remove_except(data)
                    elif action_type == "score":
                        receive_remove_score(data)
                    elif action_type == "watch":
                        receive_remove_watch(data)

                elif action == "update":
                    if action_type == "refresh":
                        receive_refresh(client, data)

            elif sender == "NOFLOOD":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOPORN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOSPAM":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "RECHECK":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "REGEX":

                if action == "regex":
                    if action_type == "update":
                        receive_regex(client, message, data)
                    elif action_type == "count":
                        if data == "ask":
                            send_count(client)

            elif sender == "WARN":

                if action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "WATCH":

                if action == "add":
                    if action_type == "watch":
                        receive_watch_user(data)

        return True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return False


def test(update: Update, context: CallbackContext) -> bool:
    # Show test results in TEST group
    glovar.locks["test"].acquire()
    try:
        client = context.bot
        message = update.effective_message

        long_test(client, message)

        return True
    except Exception as e:
        logger.warning(f"Test error: {e}", exc_info=True)
    finally:
        glovar.locks["test"].release()

    return False

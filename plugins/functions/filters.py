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
import re
from typing import Union

from telegram import Message
from telegram.ext import BaseFilter

from .. import glovar
from .etc import get_now, get_text
from .file import save
from .ids import init_group_id

# Enable logging
logger = logging.getLogger(__name__)


class FilterClassC(BaseFilter):
    # Check if the message is Class C object
    def filter(self, message: Message):
        try:
            if message.from_user:
                uid = message.from_user.id
                gid = message.chat.id
                if init_group_id(gid):
                    if uid in glovar.admin_ids[gid] or uid in glovar.bot_ids:
                        return True
        except Exception as e:
            logger.warning(f"Is class c error: {e}", exc_info=True)

        return False


class FilterClassD(BaseFilter):
    # Check if the message is Class D object
    def filter(self, message: Message):
        try:
            if message.from_user:
                uid = message.from_user.id
                if uid in glovar.bad_ids["users"]:
                    return True

            if message.forward_from:
                fid = message.forward_from.id
                if fid in glovar.bad_ids["users"]:
                    return True

            if message.forward_from_chat:
                cid = message.forward_from_chat.id
                if cid in glovar.bad_ids["channels"]:
                    return True
        except Exception as e:
            logger.warning(f"FilterClassD error: {e}", exc_info=True)

        return False


class FilterClassE(BaseFilter):
    # Check if the message is Class E object
    def filter(self, message: Message):
        try:
            if message.forward_from_chat:
                cid = message.forward_from_chat.id
                if cid in glovar.except_ids["channels"]:
                    return True
        except Exception as e:
            logger.warning(f"FilterClassE error: {e}", exc_info=True)

        return False


class FilterDeclaredMessage(BaseFilter):
    # Check if the message is declared by other bots
    def filter(self, message: Message):
        try:
            if message.chat:
                gid = message.chat.id
                mid = message.message_id
                if mid in glovar.declared_message_ids.get(gid, set()):
                    return True
        except Exception as e:
            logger.warning(f"FilterDeclaredMessage error: {e}", exc_info=True)

        return False


class FilterExchangeChannel(BaseFilter):
    # Check if the message is sent from the exchange channel
    def filter(self, message: Message):
        try:
            if message.chat:
                cid = message.chat.id
                if glovar.should_hide:
                    if cid == glovar.hide_channel_id:
                        return True
                elif cid == glovar.exchange_channel_id:
                    return True
        except Exception as e:
            logger.warning(f"FilterExchangeChannel error: {e}", exc_info=True)

        return False


class FilterFromUser(BaseFilter):
    # Check if the message is sent from a user
    def filter(self, message: Message):
        try:
            if message.from_user:
                return True
        except Exception as e:
            logger.warning(f"FilterFromUser error: {e}", exc_info=True)

        return False


class FilterHideChannel(BaseFilter):
    # Check if the message is sent from the hide channel
    def filter(self, message: Message):
        try:
            if message.chat:
                cid = message.chat.id
                if cid == glovar.hide_channel_id:
                    return True
        except Exception as e:
            logger.warning(f"FilterHideChannel error: {e}", exc_info=True)

        return False


class FilterNewGroup(BaseFilter):
    # Check if the bot joined a new group
    def filter(self, message: Message):
        try:
            new_users = message.new_chat_members
            if new_users:
                for user in new_users:
                    if user.id == glovar.long_id:
                        return True
            elif message.group_chat_created or message.supergroup_chat_created:
                return True
        except Exception as e:
            logger.warning(f"FilterNewGroup error: {e}", exc_info=True)

        return False


class FilterTestGroup(BaseFilter):
    # Check if the message is sent from the test group
    def filter(self, message: Message):
        try:
            if message.chat:
                cid = message.chat.id
                if cid == glovar.test_group_id:
                    return True
        except Exception as e:
            logger.warning(f"FilterTestGroup error: {e}", exc_info=True)

        return False


class_c = FilterClassC()

class_d = FilterClassD()

class_e = FilterClassE()

declared_message = FilterDeclaredMessage()

exchange_channel = FilterExchangeChannel()

from_user = FilterFromUser()

hide_channel = FilterHideChannel()

new_group = FilterNewGroup()

test_group = FilterTestGroup()


def is_ban_text(text: str) -> bool:
    # Check if the text is ban text
    try:
        if is_regex_text("ban", text):
            return True

        if is_regex_text("ad", text) and (is_regex_text("con", text) or is_regex_text("iml", text)):
            return True
    except Exception as e:
        logger.warning(f"Is ban text error: {e}", exc_info=True)

    return False


def is_class_c(_, message: Message) -> bool:
    # Check if the message is Class C object
    try:
        if message.from_user:
            uid = message.from_user.id
            gid = message.chat.id
            if init_group_id(gid):
                if uid in glovar.admin_ids.get(gid, set()) or uid in glovar.bot_ids or message.from_user.is_self:
                    return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the message is Class D object
    try:
        if message.from_user:
            uid = message.from_user.id
            if uid in glovar.bad_ids["users"]:
                return True

        if message.forward_from:
            fid = message.forward_from.id
            if fid in glovar.bad_ids["users"]:
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.bad_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)

    return False


def is_declared_message(message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if message.chat:
            gid = message.chat.id
            mid = message.message_id
            if mid in glovar.declared_message_ids.get(gid, set()):
                return True
    except Exception as e:
        logger.warning(f"FilterDeclaredMessage error: {e}", exc_info=True)

    return False


def is_detected_user(message: Message) -> bool:
    # Check if the message is sent by a detected user
    try:
        if message.from_user:
            gid = message.chat.id
            uid = message.from_user.id
            return is_detected_user_id(gid, uid)
    except Exception as e:
        logger.warning(f"Is detected user error: {e}", exc_info=True)

    return False


def is_detected_user_id(gid: int, uid: int) -> bool:
    # Check if the user_id is detected in the group
    try:
        user = glovar.user_ids.get(uid, {})
        if user:
            status = user["detected"].get(gid, 0)
            now = get_now()
            if now - status < glovar.time_punish:
                return True
    except Exception as e:
        logger.warning(f"Is detected user id error: {e}", exc_info=True)

    return False


def is_high_score_user(message: Message) -> Union[bool, float]:
    # Check if the message is sent by a high score user
    try:
        if message.from_user:
            uid = message.from_user.id
            user = glovar.user_ids.get(uid, {})
            if user:
                score = sum(user["score"].values())
                if score >= 3.0:
                    return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return False


def is_long_text(message: Message) -> int:
    # Check if the text is super long
    try:
        text = get_text(message)
        if not text.strip():
            return 0

        if is_detected_user(message):
            return 79

        gid = message.chat.id
        length = len(text.encode())
        if length >= glovar.configs[gid]["limit"]:
            # Work with NOSPAM
            if length <= 10000:
                if glovar.nospam_id in glovar.admin_ids[gid]:
                    if is_ban_text(text):
                        return 0

                    if is_regex_text("del", text):
                        return 0

            return length
    except Exception as e:
        logger.warning(f"Is long text error: {e}", exc_info=True)

    return False


def is_regex_text(word_type: str, text: str, again: bool = False) -> bool:
    # Check if the text hit the regex rules
    result = False
    try:
        if text:
            if not again:
                text = re.sub(r"\s{2,}", " ", text)
            elif " " in text:
                text = re.sub(r"\s", "", text)
            else:
                return False
        else:
            return False

        for word in list(eval(f"glovar.{word_type}_words")):
            if re.search(word, text, re.I | re.S | re.M):
                result = True

            # Match, count and return
            if result:
                count = eval(f"glovar.{word_type}_words").get(word, 0)
                count += 1
                eval(f"glovar.{word_type}_words")[word] = count
                save(f"{word_type}_words")
                return result

        # Try again
        return is_regex_text(word_type, text, True)
    except Exception as e:
        logger.warning(f"Is regex text error: {e}", exc_info=True)

    return result


def is_watch_user(message: Message, the_type: str) -> bool:
    # Check if the message is sent by a watch user
    try:
        if message.from_user:
            uid = message.from_user.id
            now = get_now()
            until = glovar.watch_ids[the_type].get(uid, 0)
            if now < until:
                return True
    except Exception as e:
        logger.warning(f"Is watch user error: {e}", exc_info=True)

    return False

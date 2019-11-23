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
from copy import deepcopy
from string import ascii_lowercase
from typing import Match, Optional, Union

from telegram import Message, User
from telegram.ext import BaseFilter

from .. import glovar
from .etc import get_now, get_int, get_forward_name, get_full_name, get_text
from .file import save
from .ids import init_group_id

# Enable logging
logger = logging.getLogger(__name__)


class FilterAuthorizedGroup(BaseFilter):
    # Check if the message is send from the authorized group
    def filter(self, message: Message):
        try:
            if not message.chat:
                return False

            cid = message.chat.id
            if init_group_id(cid):
                return True
        except Exception as e:
            logger.warning(f"FilterAuthorizedGroup error: {e}", exc_info=True)

        return False


class FilterClassC(BaseFilter):
    # Check if the message is sent from Class C personnel
    def filter(self, message: Message):
        try:
            if not message.from_user:
                return False

            # Basic data
            uid = message.from_user.id
            gid = message.chat.id

            # Check permission
            if uid in glovar.admin_ids[gid] or uid in glovar.bot_ids:
                return True
        except Exception as e:
            logger.warning(f"FilterClassC error: {e}", exc_info=True)

        return False


class FilterClassD(BaseFilter):
    # Check if the message is Class D object
    def filter(self, message: Message):
        try:
            if message.from_user:
                if is_class_d_user(message.from_user):
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
            if not message.chat:
                return False

            gid = message.chat.id
            mid = message.message_id
            return is_declared_message_id(gid, mid)
        except Exception as e:
            logger.warning(f"FilterDeclaredMessage error: {e}", exc_info=True)

        return False


class FilterExchangeChannel(BaseFilter):
    # Check if the message is sent from the exchange channel
    def filter(self, message: Message):
        try:
            if not message.chat:
                return False

            cid = message.chat.id
            if glovar.should_hide:
                return cid == glovar.hide_channel_id
            else:
                return cid == glovar.exchange_channel_id
        except Exception as e:
            logger.warning(f"FilterExchangeChannel error: {e}", exc_info=True)

        return False


class FilterFromUser(BaseFilter):
    # Check if the message is sent from a user
    def filter(self, message: Message):
        try:
            if message.from_user and message.from_user.id != 777000:
                return True
        except Exception as e:
            logger.warning(f"FilterFromUser error: {e}", exc_info=True)

        return False


class FilterHideChannel(BaseFilter):
    # Check if the message is sent from the hide channel
    def filter(self, message: Message):
        try:
            if not message.chat:
                return False

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
                return any(user.id == glovar.long_id for user in new_users)
            elif message.group_chat_created or message.supergroup_chat_created:
                return True
        except Exception as e:
            logger.warning(f"FilterNewGroup error: {e}", exc_info=True)

        return False


class FilterTestGroup(BaseFilter):
    # Check if the message is sent from the test group
    def filter(self, message: Message):
        try:
            if not message.chat:
                return False

            cid = message.chat.id
            if cid == glovar.test_group_id:
                return True
        except Exception as e:
            logger.warning(f"FilterTestGroup error: {e}", exc_info=True)

        return False


authorized_group = FilterAuthorizedGroup()

class_c = FilterClassC()

class_d = FilterClassD()

class_e = FilterClassE()

declared_message = FilterDeclaredMessage()

exchange_channel = FilterExchangeChannel()

from_user = FilterFromUser()

hide_channel = FilterHideChannel()

new_group = FilterNewGroup()

test_group = FilterTestGroup()


def is_ad_text(text: str, ocr: bool, matched: str = "") -> str:
    # Check if the text is ad text
    try:
        if not text:
            return ""

        for c in ascii_lowercase:
            if c != matched and is_regex_text(f"ad{c}", text, ocr):
                return c
    except Exception as e:
        logger.warning(f"Is ad text error: {e}", exc_info=True)

    return ""


def is_ban_text(text: str, ocr: bool, message: Message = None) -> bool:
    # Check if the text is ban text
    try:
        if is_regex_text("ban", text, ocr):
            return True

        ad = is_regex_text("ad", text, ocr) or is_emoji("ad", text, message)
        con = is_con_text(text, ocr)
        if ad and con:
            return True

        ad = is_ad_text(text, ocr)
        if ad and con:
            return True

        if ad:
            ad = is_ad_text(text, ocr, ad)
            return bool(ad)
    except Exception as e:
        logger.warning(f"Is ban text error: {e}", exc_info=True)

    return False


def is_class_c(_, message: Message) -> bool:
    # Check if the message is Class C object
    try:
        if not message.from_user:
            return False

        # Basic data
        uid = message.from_user.id
        gid = message.chat.id

        # Check permission
        if uid in glovar.admin_ids[gid] or uid in glovar.bot_ids:
            return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the message is Class D object
    try:
        if message.from_user:
            if is_class_d_user(message.from_user):
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


def is_class_d_user(user: Union[int, User]) -> bool:
    # Check if the user is a Class D personnel
    try:
        if isinstance(user, int):
            uid = user
        else:
            uid = user.id

        if uid in glovar.bad_ids["users"]:
            return True
    except Exception as e:
        logger.warning(f"Is class d user error: {e}", exc_info=True)

    return False


def is_class_e_user(user: Union[int, User]) -> bool:
    # Check if the user is a Class E personnel
    try:
        if isinstance(user, int):
            uid = user
        else:
            uid = user.id

        group_list = list(glovar.admin_ids)
        for gid in group_list:
            if uid in glovar.admin_ids.get(gid, set()):
                return True
    except Exception as e:
        logger.warning(f"Is class e user error: {e}", exc_info=True)

    return False


def is_con_text(text: str, ocr: bool) -> bool:
    # Check if the text is con text
    try:
        if (is_regex_text("con", text, ocr)
                or is_regex_text("aff", text, ocr)
                or is_regex_text("iml", text, ocr)
                or is_regex_text("pho", text, ocr)):
            return True
    except Exception as e:
        logger.warning(f"Is con text error: {e}", exc_info=True)

    return False


def is_declared_message(message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if not message.chat:
            return False

        gid = message.chat.id
        mid = message.message_id
        return is_declared_message_id(gid, mid)
    except Exception as e:
        logger.warning(f"Is declared message error: {e}", exc_info=True)

    return False


def is_declared_message_id(gid: int, mid: int) -> bool:
    # Check if the message's ID is declared by other bots
    try:
        if mid in glovar.declared_message_ids.get(gid, set()):
            return True
    except Exception as e:
        logger.warning(f"Is declared message id error: {e}", exc_info=True)

    return False


def is_detected_user(message: Message) -> bool:
    # Check if the message is sent by a detected user
    try:
        if not message.from_user:
            return False

        gid = message.chat.id
        uid = message.from_user.id
        now = get_int(message.date.strftime("%s")) or get_now()
        return is_detected_user_id(gid, uid, now)
    except Exception as e:
        logger.warning(f"Is detected user error: {e}", exc_info=True)

    return False


def is_detected_user_id(gid: int, uid: int, now: int) -> bool:
    # Check if the user_id is detected in the group
    try:
        user_status = glovar.user_ids.get(uid, {})

        if not user_status:
            return False

        status = user_status["detected"].get(gid, 0)
        if now - status < glovar.time_punish:
            return True
    except Exception as e:
        logger.warning(f"Is detected user id error: {e}", exc_info=True)

    return False


def is_emoji(the_type: str, text: str, message: Message = None) -> bool:
    # Check the emoji type
    try:
        if message:
            text = get_text(message, False, False)

        emoji_dict = {}
        emoji_set = {emoji for emoji in glovar.emoji_set if emoji in text and emoji not in glovar.emoji_protect}
        emoji_old_set = deepcopy(emoji_set)

        for emoji in emoji_old_set:
            if any(emoji in emoji_old and emoji != emoji_old for emoji_old in emoji_old_set):
                emoji_set.discard(emoji)

        for emoji in emoji_set:
            emoji_dict[emoji] = text.count(emoji)

        # Check ad
        if the_type == "ad":
            if any(emoji_dict[emoji] >= glovar.emoji_ad_single for emoji in emoji_dict):
                return True

            if sum(emoji_dict.values()) >= glovar.emoji_ad_total:
                return True

        # Check many
        elif the_type == "many":
            if sum(emoji_dict.values()) >= glovar.emoji_many:
                return True

        # Check wb
        elif the_type == "wb":
            if any(emoji_dict[emoji] >= glovar.emoji_wb_single for emoji in emoji_dict):
                return True

            if sum(emoji_dict.values()) >= glovar.emoji_wb_total:
                return True
    except Exception as e:
        logger.warning(f"Is emoji error: {e}", exc_info=True)

    return False


def is_high_score_user(user: User) -> float:
    # Check if the message is sent by a high score user
    try:
        if is_class_e_user(user):
            return 0.0

        uid = user.id
        user_status = glovar.user_ids.get(uid, {})

        if not user_status:
            return 0.0

        score = sum(user_status["score"].values())
        if score >= 3.0:
            return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return 0.0


def is_limited_user(gid: int, user: User, now: int, short: bool = True) -> bool:
    # Check the user is limited
    try:
        if is_class_e_user(user):
            return False

        if glovar.configs[gid].get("new"):
            if is_new_user(user, now, gid):
                return True

        uid = user.id

        if not glovar.user_ids.get(uid, {}):
            return False

        if not glovar.user_ids[uid].get("join", {}):
            return False

        if is_high_score_user(user) >= 1.8:
            return True

        join = glovar.user_ids[uid]["join"].get(gid, 0)
        if short and now - join < glovar.time_short:
            return True

        track = [gid for gid in glovar.user_ids[uid]["join"]
                 if now - glovar.user_ids[uid]["join"][gid] < glovar.time_track]

        if len(track) >= glovar.limit_track:
            return True
    except Exception as e:
        logger.warning(f"Is limited user error: {e}", exc_info=True)

    return False


def is_long_text(message: Message) -> int:
    # Check if the text is super long
    try:
        if not message.chat:
            return 0

        # Basic data
        gid = message.chat.id

        # Get text
        text = get_text(message)
        if not text.strip():
            return 0

        # If the user is being punished
        if is_detected_user(message):
            return 79

        # Get length
        length = len(text.encode())

        # Check limit
        if length < glovar.configs[gid]["limit"]:
            return 0

        # Work with NOSPAM
        if length <= 10000:
            # Check the forward from name:
            forward_name = get_forward_name(message, True)
            if is_nm_text(forward_name):
                return 0

            # Check the user's name:
            name = get_full_name(message.from_user, True)
            if is_nm_text(name):
                return 0

            # Check the text
            normal_text = get_text(message, True)
            if glovar.nospam_id in glovar.admin_ids[gid]:
                if is_ban_text(normal_text, False):
                    return 0

                if is_regex_text("del", normal_text):
                    return 0

            return length
    except Exception as e:
        logger.warning(f"Is long text error: {e}", exc_info=True)

    return 0


def is_new_user(user: User, now: int, gid: int = 0, joined: bool = False) -> bool:
    # Check if the message is sent from a new joined member
    try:
        if is_class_e_user(user):
            return False

        uid = user.id

        if not glovar.user_ids.get(uid, {}):
            return False

        if not glovar.user_ids[uid].get("join", {}):
            return False

        if joined:
            return True

        if gid:
            join = glovar.user_ids[uid]["join"].get(gid, 0)
            if now - join < glovar.time_new:
                return True
        else:
            for gid in list(glovar.user_ids[uid]["join"]):
                join = glovar.user_ids[uid]["join"].get(gid, 0)
                if now - join < glovar.time_new:
                    return True
    except Exception as e:
        logger.warning(f"Is new user error: {e}", exc_info=True)

    return False


def is_nm_text(text: str) -> bool:
    # Check if the text is nm text
    try:
        if (is_regex_text("nm", text)
                or is_regex_text("bio", text)
                or is_ban_text(text, False)):
            return True
    except Exception as e:
        logger.warning(f"Is nm text error: {e}", exc_info=True)

    return False


def is_regex_text(word_type: str, text: str, ocr: bool = False, again: bool = False) -> Optional[Match]:
    # Check if the text hit the regex rules
    result = None
    try:
        if text:
            if not again:
                text = re.sub(r"\s{2,}", " ", text)
            elif " " in text:
                text = re.sub(r"\s", "", text)
            else:
                return None
        else:
            return None

        with glovar.locks["regex"]:
            words = list(eval(f"glovar.{word_type}_words"))

        for word in words:
            if ocr and "(?# nocr)" in word:
                continue

            result = re.search(word, text, re.I | re.S | re.M)

            # Count and return
            if result:
                count = eval(f"glovar.{word_type}_words").get(word, 0)
                count += 1
                eval(f"glovar.{word_type}_words")[word] = count
                save(f"{word_type}_words")
                return result

        # Try again
        return is_regex_text(word_type, text, ocr, True)
    except Exception as e:
        logger.warning(f"Is regex text error: {e}", exc_info=True)

    return result


def is_watch_user(user: User, the_type: str, now: int) -> bool:
    # Check if the message is sent by a watch user
    try:
        if is_class_e_user(user):
            return False

        uid = user.id
        until = glovar.watch_ids[the_type].get(uid, 0)
        if now < until:
            return True
    except Exception as e:
        logger.warning(f"Is watch user error: {e}", exc_info=True)

    return False

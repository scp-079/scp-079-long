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
from typing import List, Optional, Union

from telegram import Bot, Chat, ChatMember, ChatPermissions, InlineKeyboardMarkup, Message, ParseMode
from telegram.error import BadRequest

from .. import glovar
from .etc import delay

# Enable logging
logger = logging.getLogger(__name__)


def delete_message(client: Bot, cid: int, mid: int) -> Optional[bool]:
    # Delete some messages
    result = None
    try:
        if not cid or not mid:
            return None

        result = client.delete_message(chat_id=cid, message_id=mid)
    except Exception as e:
        logger.warning(f"Delete message {mid} in {cid} error: {e}", exc_info=True)

    return result


def download_media(client: Bot, file_id: str, file_path: str):
    # Download a media file
    result = None
    try:
        file = client.get_file(file_id=file_id)
        if not file:
            return None

        downloaded = file.download(custom_path=file_path)
        if downloaded:
            result = file_path
    except Exception as e:
        logger.warning(f"Download media {file_id} to {file_path} error: {e}", exc_info=True)

    return result


def get_admins(client: Bot, cid: int) -> Optional[Union[bool, List[ChatMember]]]:
    # Get a group's admins
    result = None
    try:
        try:
            result = client.get_chat_administrators(chat_id=cid)
        except BadRequest:
            return False
    except Exception as e:
        logger.warning(f"Get admins in {cid} error: {e}", exc_info=True)

    return result


def get_chat_member(client: Bot, cid: int, uid: int) -> Optional[Union[bool, ChatMember]]:
    # Get a chat member
    result = None
    try:
        try:
            result = client.get_chat_member(chat_id=cid, user_id=uid)
        except BadRequest:
            return False
    except Exception as e:
        logger.warning(f"Get chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


def get_group_info(client: Bot, chat: Union[int, Chat]) -> (str, str):
    # Get a group's name and link
    group_name = "Unknown Group"
    group_link = glovar.default_group_link
    try:
        if isinstance(chat, int):
            result = None
            try:
                result = client.get_chat(chat_id=chat)
            except Exception as e:
                logger.info(f"Get chat {chat} error: {e}", exc_info=True)

            chat = result

        if chat.title:
            group_name = chat.title

        if chat.username:
            group_link = "https://t.me/" + chat.username
    except Exception as e:
        logger.info(f"Get group info error: {e}", exc_info=True)

    return group_name, group_link


def kick_chat_member(client: Bot, cid: int, uid: int) -> Optional[bool]:
    # Kick a chat member in a group
    result = None
    try:
        result = client.kick_chat_member(chat_id=cid, user_id=uid)
    except Exception as e:
        logger.warning(f"Kick chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


def leave_chat(client: Bot, cid: int) -> Optional[bool]:
    # Leave a channel
    result = None
    try:
        result = client.leave_chat(chat_id=cid)
    except Exception as e:
        logger.warning(f"Leave chat {cid} error: {e}", exc_info=True)

    return result


def restrict_chat_member(client: Bot, cid: int, uid: int, permissions: ChatPermissions,
                         until_date: int = 0) -> bool:
    # Restrict a user in a supergroup
    result = None
    try:
        result = client.restrict_chat_member(
            chat_id=cid,
            user_id=uid,
            until_date=until_date,
            permissions=permissions
        )
    except Exception as e:
        logger.warning(f"Restrict chat member error: {e}", exc_info=True)

    return result


def send_document(client: Bot, cid: int, document: str, caption: str = None, mid: int = None,
                  markup: InlineKeyboardMarkup = None) -> Optional[Union[bool, Message]]:
    # Send a document to a chat
    result = None
    try:
        try:
            with open(document, "rb") as f:
                result = client.send_document(
                    chat_id=cid,
                    document=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=mid,
                    reply_markup=markup
                )
        except BadRequest:
            return False
    except Exception as e:
        logger.warning(f"Send document to {cid} error: {e}", exec_info=True)

    return result


def send_message(client: Bot, cid: int, text: str, mid: int = None,
                 markup: InlineKeyboardMarkup = None) -> Optional[Union[bool, Message]]:
    # Send a message to a chat
    result = None
    try:
        if not text.strip():
            return None

        try:
            result = client.send_message(
                chat_id=cid,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_to_message_id=mid,
                reply_markup=markup
            )
        except BadRequest:
            return False
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result


def send_report_message(secs: int, client: Bot, cid: int, text: str, mid: int = None,
                        markup: InlineKeyboardMarkup = None) -> Optional[Message]:
    # Send a message that will be auto deleted to a chat
    result = None
    try:
        if not text.strip():
            return None

        result = client.send_message(
            chat_id=cid,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_to_message_id=mid,
            reply_markup=markup
        )

        if not result:
            return None

        mid = result.message_id
        delay(secs, delete_message, [client, cid, mid])
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result

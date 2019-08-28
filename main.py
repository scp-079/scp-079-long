#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater

from plugins import glovar
from plugins.functions.timers import backup_files, reset_data, send_count, update_admins, update_status
from plugins.handlers.command import add_command_handlers
from plugins.handlers.error import add_error_handlers
from plugins.handlers.message import add_message_handlers

# Enable logging
logger = logging.getLogger(__name__)

# Create the EventHandler
updater = Updater(
    token=glovar.bot_token,
    request_kwargs=glovar.request_kwargs,
    use_context=True
)

# Register handlers
add_command_handlers(updater.dispatcher)
add_message_handlers(updater.dispatcher)
add_error_handlers(updater.dispatcher)

# Timer
scheduler = BackgroundScheduler()
scheduler.add_job(update_status, "cron", [updater.bot], minute=30)
scheduler.add_job(backup_files, "cron", [updater.bot], hour=20)
scheduler.add_job(send_count, "cron", [updater.bot], hour=21)
scheduler.add_job(reset_data, "cron", day=glovar.reset_day, hour=22)
scheduler.add_job(update_admins, "cron", [updater.bot], hour=22, minute=30)
scheduler.start()

# Start the Bot
updater.start_polling()

# Run the bot until press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
updater.idle()

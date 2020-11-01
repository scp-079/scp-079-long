#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SCP-079-LONG - Control super long messages
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
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
from random import randint

from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater

from plugins import glovar
from plugins.functions.timers import backup_files, interval_min_10, reset_data, send_count, update_admins, update_status
from plugins.handlers.command import add_command_handlers
from plugins.handlers.error import add_error_handlers
from plugins.handlers.message import add_message_handlers

# Enable logging
logger = logging.getLogger(__name__)

# Config session
updater = Updater(
    token=glovar.bot_token,
    request_kwargs=glovar.request_kwargs,
    use_context=True
)
updater.start_polling()

# Register handlers
add_command_handlers(updater.dispatcher)
add_message_handlers(updater.dispatcher)
add_error_handlers(updater.dispatcher)

# Send online status
update_status(updater.bot, "online")

# Timer
scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 60})
scheduler.add_job(interval_min_10, "interval", minutes=10)
scheduler.add_job(update_status, "cron", [updater.bot, "awake"], minute=randint(30, 34), second=randint(0, 59))
scheduler.add_job(backup_files, "cron", [updater.bot], hour=20)
scheduler.add_job(send_count, "cron", [updater.bot], hour=21)
scheduler.add_job(reset_data, "cron", [updater.bot], day=glovar.date_reset, hour=22)
scheduler.add_job(update_admins, "cron", [updater.bot], hour=22, minute=30)
scheduler.start()

# Hold
updater.idle()

# Stop
updater.stop()

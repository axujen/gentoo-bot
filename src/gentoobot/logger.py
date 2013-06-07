#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# © Copyright 2013 axujen, <axujen at gmail.com>. All Rights Reserved.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from glob import glob
from collections import defaultdict
import logging
import logging.handlers


# Console log
logger = logging.getLogger('console')
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(logging.INFO)

cformat = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M")
console.setFormatter(cformat)
logger.addHandler(console)

# Channel logs
ch_format = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

from config import config_base

def log_event(server, event):
	type = event.type
	source = event.source
	target = event.target
	arguments = event.arguments
	msg = '(%s from %s to %s) %s' % (type, source, target,
			'; '.join([arg for arg in arguments]))
	logger.info(msg)
	chat_log(server, type, source, target, arguments)

def error_log(exception, server=None):
	"""Per server error log"""
	if server:
		log = logging.getLogger(server)
		if not os.path.exists(os.path.join(config_base, server)):
				os.makedirs(os.path.join(config_base, server))
		logfile = os.path.join(config_base, server, 'errors.log')
	else:
		log = logging.getLogger('errors')
		logfile = os.path.join(config_base, 'errors.log')

	if not log.handlers:
		filehandler = logging.FileHandler(logfile)
		filehandler.setLevel(logging.ERROR)
		filehandler.setFormatter(cformat)
		log.addHandler(filehandler)

	logger.exception(exception)
	log.exception(exception)

def chat_log(server, type, source, target, arguments):
	logdir = os.path.join(config_base, server, 'logs')
	if not os.path.exists(logdir):
		os.makedirs(logdir)

	if target == None or type == 'nick':
		# 2deep4me
		channels = [os.path.split(ch)[1][:-4] for ch in glob("%s%s%s" % (logdir, os.path.sep, "*.log")) if os.path.isfile(ch)]
	elif target.startswith('#'):
		channels = [target.replace(os.path.sep, '_')[1:]]
	else: return

	for channel in channels:
		logfile = os.path.join(logdir, channel+'.log')
		log = logging.getLogger(channel)

		if not log.handlers:
			handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=4000000,
					backupCount=50)
			handler.setLevel(logging.CRITICAL)
			handler.setFormatter(ch_format)
			log.addHandler(handler)

		entry = format_log(type, source, target, arguments)
		if entry:
			log.critical(entry)

def format_log(type, source, target, arguments):
	"""Format a channel msg and return a good looking entry"""
	entry = None
	if type in ('pubmsg', 'privmsg'):
		entry = "%s\t%s" % (source.nick, arguments[0])
	elif type in ('pubnotice', 'privnotice'):
		entry = '-- Notice(%s) -> %s: %s' % (source.nick, target, arguments[0])
	elif type == 'join':
		entry = "--> %s (%s) has joined the channel" % (source.nick, source)
	elif type == 'part':
		entry = "<-- %s (%s) has left the channel" % (source.nick, source)
	elif type == 'kick':
		entry = '<-- %s has kicked %s from the channel (%s)' % (source.nick, arguments[0], arguments[1])
	elif type == 'quit':
		entry = '<-- %s (%s) has quit (%s) ' % (source.nick, source, arguments[0])
	elif type == 'action':
		entry = '\t*\t%s %s' % (source.split('!')[0], arguments[0])
	elif type == 'nick':
		entry = '-- %s (%s) is now known as %s' % (source.nick, source, target)
	elif type == 'mode':
		entry = '-- Mode %s [ %s %s ] by %s' % (target, arguments[0], arguments[1], source.nick)
	return entry

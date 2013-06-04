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

import os.path
from os import mkdir
from time import localtime, strftime
from collections import defaultdict
from config import config_base

global chan_buf, raw_buf, buf_len
chan_buf = defaultdict(dict)
raw_buf = defaultdict(list)
buf_len = 10

def log(server, event, verbose):
	entry = parse_event(event)
	write_log(server, event, entry)
	if verbose: print(entry)
	return

def parse_event(event):
	"""Parse an event and return a suitable entry for writting"""

	timestamp = strftime('%H:%M', localtime())
	msg = ''
	if len(event.arguments) > 0: msg = event.arguments[0]
	type = event.type.upper()
	target = event.target
	source = event.source
	if hasattr(source, 'nick'):
		source = source.nick

	entry = "(%s) to %s from %s | %s" % (type, target, source, msg)

	if type in ('JOIN', 'PART'):
		entry = "(%s) %s %sed %s" % (type, source, type.lower(), target)
	elif type == 'QUIT':
		entry = "(%s) %s disconnected saying %s" % (type, source, msg)
	elif type == 'NICK':
		oldnick = source.nick
		entry = "(%s) %s is now known as %s" % (type, oldnick, target)
	elif type == 'MODE':
		t = event.arguments[1]
		entry = "(%s) %s changed %s mode in %s %s" % (type, source, t, target, msg)
	elif type == "TOPIC":
		entry = "(%s) %s changed %s topic to %s" % (type, source, target, msg)

	return '[%s] %s' % (timestamp, entry)

def write_log(server, event, entry):
	"""Categorieze logs and write to file after buffering enough lines."""
	if str(event.target).startswith('#'):
		channel_log(server, entry, str(event.target))
	raw_log(server, entry)

def channel_log(server, entry, channel):
	if not channel in chan_buf[server]:
		chan_buf[server] = defaultdict(list)

	chan_buf[server][channel].append(entry)
	if len(chan_buf[server][channel]) > buf_len:
		_write_chan(server, channel)

def raw_log(server, entry):
	"""Write raw uncategorized log"""
	raw_buf[server].append(entry)
	if len(raw_buf[server]) >= buf_len:
		_write_raw(server)

def _write_chan(server, channel):
	logdir = os.path.join(config_base, server, 'logs')

	if not os.path.exists(logdir):
		mkdir(logdir)

	if not os.path.isdir(logdir):
		raise ValueError("%s is not a directory." % logdir)

	with open(os.path.join(logdir, channel.replace(os.path.sep, '_')), 'a') as log:
		for line in chan_buf[server][channel]:
			log.write(line+'\n')

	del(chan_buf[server][channel])

def _write_raw(server):
	logdir = os.path.join(config_base, server, 'logs')

	if not os.path.exists(logdir):
		mkdir(logdir)

	if not os.path.isdir(logdir):
		raise ValueError("%s is not a directory." % logdir)

	with open(os.path.join(logdir, 'raw'), 'a') as log:
		for line in raw_buf[server]:
			log.write(line+'\n')
	del(raw_buf[server])

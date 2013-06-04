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
from os import makedirs
from ConfigParser import ConfigParser
from argparse import ArgumentParser
import json

# Config defaults.
config = ConfigParser()
global config_base
config_base = "$HOME/.gentoobot"
config_base = os.path.normpath(os.path.expandvars(os.path.expanduser(config_base)))

config.add_section('LASTFM')
config.set('LASTFM', 'api_pub',		'1af49b4138e72da18bae9e77f1af46aa')
config.set('LASTFM', 'api_secret',	'3421bd09678c3a191310c5433017e4a6')

config.add_section('CONNECTION')
config.set('CONNECTION', 'port',	'6667')
config.set('CONNECTION', 'server',	'irc.installgentoo.com')
config.set('CONNECTION', 'nick',	'GentooTestBot')
config.set('CONNECTION', 'channel',	'#/g/test')

config.add_section('MISC')
config.set('MISC',	'verbose',	'false')
config.set('MISC',	'reconnect', '5')

# Arguments
arguments = ArgumentParser(argument_default=None)
arguments.add_argument('-s', '--server', dest='server', help='irc server to connect to')
arguments.add_argument('-p', '--port', type=int, dest='port', help='server port')
arguments.add_argument('-c', '--channel', dest='channel', help='channel to join')
arguments.add_argument('-n', '--nick', dest='nick', help="bot's nick")
arguments.add_argument('-r', '--reconnect', dest='reconnect', type=int,
		help='reconnection interval when kicked from a channel or when disconnected')
arguments.add_argument('-v', '--verbose', dest='verbose', action='store_true',
		default=None, help='toggle verbose mode')
arguments.add_argument('--config', dest='config', default=config_base,
	help='specify an alternative config folder')

def get_config(section):
	"""Return a dictionary with options necessary for running the bot"""

	args = vars(arguments.parse_args())
	config_base = os.path.normpath(os.path.expanduser(os.path.expandvars(args['config'])))

	if not os.path.exists(config_base):
		makedirs(config_base)

	if not os.path.isdir(config_base):
		raise ValueError('%s is not a directory' % config_base)

	configfile = os.path.join(config_base, 'config.cfg')

	if not os.path.exists(configfile):
		print('Creating new configuration file "%s"' % configfile)
		with open(configfile, 'wb') as f:
			config.write(f)
	else:
		config.read(configfile)


	opt = dict(config.items(section.upper()))

	if section.upper() == 'MISC':
		opt['verbose'] = config.getboolean('MISC', 'verbose')

	for arg in args:
		if not args[arg] == None:
			opt[arg] = args[arg]

	return opt

def save_db(server, db, object):
	"""Save a database (json) inside a folder."""
	folder = os.path.join(config_base, server)

	if not os.path.exists(folder):
		print('Creating new server db folder "%s"' % folder)
		makedirs(folder)

	if not os.path.isdir(folder):
		raise ValueError('"%s" is not a directory' % folder)

	db_file = os.path.join(folder, db)

	if os.path.exists(db_file) and not os.path.isfile(db_file):
		raise ValueError('"%s" is not a file' % db_file)

	with open(db_file, 'w') as db_file:
		json.dump(object, db_file)

def load_db(server, db):
	"""Load a json database."""
	db_file = os.path.join(config_base, server, db)
	print('Loading '+db_file)

	if not os.path.exists(db_file) or not os.path.isfile(db_file):
		return None

	with open(db_file, 'r') as db_file:
		return json.load(db_file)

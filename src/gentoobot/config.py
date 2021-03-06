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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.	If not, see <http://www.gnu.org/licenses/>.

import os, json
from ConfigParser import ConfigParser
from argparse import ArgumentParser
from ast import literal_eval


# Config defaults.
config = ConfigParser()
config_base = '$HOME/.gentoobot/'
config_base = os.path.normpath(os.path.expandvars(os.path.expanduser(config_base)))
stored_conf = {}

config.add_section('LASTFM')
config.set('LASTFM', 'api_pub',		'af6a640a95ace00ee058282b70846ba0')
config.set('LASTFM', 'api_secret',	'1f8545b425f3f0de178a61c974732057')

config.add_section('CONNECTION')
config.set('CONNECTION', 'channel',		'#Gentoobot')
config.set('CONNECTION', 'nick',		'GentooTestBot')
config.set('CONNECTION', 'password',	'None')
config.set('CONNECTION', 'port',		'6667')
config.set('CONNECTION', 'reconnect',	'5')
config.set('CONNECTION', 'server',		'irc.rizon.net')

config.add_section('OPTIONS')
config.set('OPTIONS', 'chattiness', '5')
config.set('OPTIONS', 'verbose',	'False')

# Arguments
arguments = ArgumentParser(argument_default=None)
arguments.add_argument('-s', '--server', dest='server', help='irc server to connect to')
arguments.add_argument('-p', '--port', type=int, dest='port', help='server port')
arguments.add_argument('-c', '--channel', dest='channel', help='channel to join')
arguments.add_argument('-n', '--nick', dest='nick', help="bot's nick")
arguments.add_argument('--pass', dest='password', help='Bots login password')
arguments.add_argument('-r', '--reconnect', dest='reconnect', type=int,
		help='reconnection interval when kicked from a channel or when disconnected')
arguments.add_argument('--config', dest='config', default=config_base,
	help='specify an alternative config folder')
arguments.add_argument('-v', '--verbose', dest='verbose', action='store_true',
		default=None, help='Turn on verbose output')

from gentoobot.logger import logger

def get_config(section):
	"""Return a dictionary with options necessary for running the bot"""

	global config_base, stored_conf
	section = section.upper()
	if not section in stored_conf:
		args = vars(arguments.parse_args())
		config_base = os.path.normpath(os.path.expanduser(os.path.expandvars(args['config'])))
		configfile = os.path.join(config_base, 'config.cfg')

		if not os.path.exists(config_base):
			logger.warning('Creating new configuration directory %s' % config_base)
			os.makedirs(config_base)

		if not os.path.isdir(config_base):
			raise ValueError('%s is not a directory' % config_base)

		if not os.path.exists(configfile):
			logger.warning('Creating new configuration file "%s"' % configfile)
			with open(configfile, 'wb') as f:
				config.write(f)
		else:
			logger.warning('Loading configuration from %s' % configfile)
			config.read(configfile)

		for section in config.sections():
			options = dict(config.items(section))
			for opt in options:
				try:
					options[opt] = literal_eval(options[opt])
				except (ValueError, SyntaxError):
					continue
			for arg in args:
				if not args[arg] == None:
					options[arg] = args[arg]
			stored_conf[section] = options
	return stored_conf[section]

def save_db(server, db, object):
	"""Save a database (json) inside a folder."""
	folder = os.path.join(config_base, server)

	if not os.path.exists(folder):
		logger.warning('Creating new server db folder "%s"' % folder)
		os.makedirs(folder)

	if not os.path.isdir(folder):
		raise ValueError('"%s" is not a directory' % folder)

	db_file = os.path.join(folder, db)

	if os.path.exists(db_file) and not os.path.isfile(db_file):
		raise ValueError('"%s" is not a file' % db_file)

	with open(db_file, 'w') as db_file:
		json.dump(object, db_file, indent=4)

def load_db(server, db):
	"""Load a json database."""
	db_file = os.path.join(config_base, server, db)
	logger.info('Loading '+db_file)

	if not os.path.exists(db_file) or not os.path.isfile(db_file):
		return None

	with open(db_file, 'r') as db_file:
		return json.load(db_file)

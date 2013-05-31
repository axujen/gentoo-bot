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

from configparser import ConfigParser
import json
import os.path
from os import mkdir

config_folder = "$HOME/.gentoobot/"

# Is there a simpler way?
config_folder = os.path.expanduser(
		os.path.expandvars(
			os.path.normpath(config_folder)))

configrc = os.path.join(config_folder, 'config')
config = ConfigParser()

# If the config dir doesn't exist make it.
if not os.path.exists(config_folder):
	mkdir(config_folder)
# If its not a folder raise an error.
elif not os.path.isdir(config_folder):
	raise ValueError("Configuration folder must be a folder!")

# Config defaults.
config['LASTFM'] = {
		'api_pub'	: '1af49b4138e72da18bae9e77f1af46aa',
		'api_secret': '3421bd09678c3a191310c5433017e4a6',}
config['CONNECTION'] = {
		'server':	'irc.installgentoo.com',
		'port'	:	'6667',
		'nick'	:	'GentooTestBot',
		'channel':	'#/g/test',}

def get_conf(section):
	"""General method to read configparser config file."""
	if os.path.exists(configrc):
		config.read(configrc)
	else:
		with open(configrc, 'w') as configfile:
			config.write(configfile)
	return dict(config[section.upper()])

def db_save(file, object):
	"""Save a `object` into a json `file`"""
	file = os.path.join(config_folder, file)
	if not os.path.exists(file):
		open(file, 'a').close()
	with open(file, 'w') as f:
		json.dump(object, f, indent=4)

def db_load(file):
	"""Load a an object from a json `file`"""
	if not os.path.exists(file):
		return False
	with open(file, 'r') as f:
		return json.load(f)

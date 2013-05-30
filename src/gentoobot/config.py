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
import os.path
from os import mkdir
config_folder = "$HOME/.gentoobot/"

# Is there a simpler way?
config_folder = os.path.expanduser(
		os.path.expandvars(
			os.path.normpath(config_folder)))

config = ConfigParser()
config['LASTFM'] = {'api_pub' : '1af49b4138e72da18bae9e77f1af46aa',
					'api_secret' : '3421bd09678c3a191310c5433017e4a6',}

if os.path.exists(config_folder):
	if not os.path.isdir(config_folder):
		raise ValueError("configuration folder my be a folder!")
else:
	mkdir(config_folder)

options = os.path.join(config_folder, "options.rc")
if os.path.exists(options):
	config.read(options)
else:
	with open(options, 'wt') as opt:
		config.write(opt)

lastfm = dict(config['LASTFM'])

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

from argparse import ArgumentParser, REMAINDER

from pylast import LastFMNetwork
from pylast import WSError
import gentoobot.config as config

# Lastfm instance
last_opt = config.get_conf('lastfm')

class commands(object):
	def __init__(self):
		self.parser = ArgumentParser(prefix_chars=':', add_help=False)
		self.commands = {}
		self.lastfm = LastFMNetwork(api_key = last_opt['api_pub'],
				api_secret = last_opt['api_secret'])

	def add_command(self, command, help, nargs=0):
		"""docstring for add_command"""
		self.parser.add_argument(command, help=help, dest=command[1:],
				nargs=REMAINDER)
		self.commands[command[1:]] = (help, nargs)

	def _parse_commands(self, message):
		"""docstring for parse_commands"""
		cmds = vars(self.parser.parse_known_args(message.split())[0])
		for cmd in cmds:
			if not cmds[cmd] == None:
				return cmd, cmds[cmd]
		else:
			raise ValueError

	def exec_command(self, event):
		msg = event.arguments[0]
		try:
			command, arguments = self._parse_commands(msg)
		except ValueError:
			return

		for cmd in self.commands:
			if command == cmd:
				return self._execute(command, arguments, event)
		raise ValueError('Unknown command %s' % command)

	def _execute(self, command, arguments, event):
		"""docstring for execute"""
		if len(arguments) < self.commands[command][1]:
			return "Not enough arguments!"

		do_cmd = 'do_'+command
		return getattr(self, do_cmd)(arguments, event)

	def do_help(self, arguments, event):
		"""docstring for do_help"""
		if not arguments:
			cmds = ', '.join([':'+cmd for cmd in self.commands.keys()])
			return 'Available commands are: %s.\nTry :help command for command'\
					' specific help.' % cmds
		else:
			cmd = arguments[0]
			for command in self.commands:
				if command in (cmd, cmd[1:]):
					return self.commands[command][0]
			return "Unknown command %s!" % cmd

class user_commands(commands):
	def __init__(self):
		super().__init__()
		self.add_command(':help', 'Show this help message.')
		lastfm_users = config.db_load('lastfm_users')
		if lastfm_users == False:
			self.lastfm_users = {}
		else:
			self.lastfm_users = lastfm_users

	def do_compare(self, arguments, event):
		"""Compare 2 lastfm users."""
		if len(arguments) > 1:
			comparer = arguments[1]
		elif event.source in self.lastfm_users:
			comparer = self.lastfm_users[event.source]
		else:
			comparer = event.source.nick

		user = arguments[0]
		try:
			comparer = self.lastfm.get_user(comparer)
			compare = comparer.compare_with_user(user)
		except WSError as e:
			return str(e)
		rating = float(compare[0])*100
		rating = int(rating)
		common_artists = compare[1]
		if common_artists:
			common_artists = ', '.join([artist.name for artist in compare[1]])
		else:
			common_artists = 'None!'

		return("Compatibility between %s and %s is %d%%! Common artists are: %s"\
					% (comparer, user, rating, common_artists))

	def do_np(self, arguments, event):
		"""Playing current or last playing song by the user."""
		if len(arguments):
			user = arguments[0]
		elif event.source in self.lastfm_users:
			user = self.lastfm_users[event.source]
		else:
			user = event.source.nick

		user = self.lastfm.get_user(user)
		try:
			np = user.get_now_playing()
		except WSError as e:
			return str(e)
		if not np:
			last_song = user.get_recent_tracks(2)[0][0]
			return("%s last played: %s" % (user, last_song))
		else:
			return("%s is playing: %s" % (user, np))

	def do_fm_register(self, arguments, event):
		"""Register a nick to a username."""
		source = event.source
		user = self.lastfm.get_user(arguments[0])
		try:
			user.get_id()
		except WSError as e:
			return str(e)
		self.lastfm_users[source] = user.name
		config.db_save("lastfm_users", self.lastfm_users)
		return "%s registered to http://lastfm.com/user/%s.\nTo update username "\
				"reissue this command." % (source, user)

commands = user_commands()
commands.add_command(':np', ':np\nThis command will show the current song '\
		'playing in your lastfm profile', 0)
commands.add_command(':compare', ":compare `user1` `user2`\nThis command will "\
		"compare user1 to user2's lastfm profiles", 1)
commands.add_command(':fm_register', 'usage: :fm_register `lastfm username`\n'\
		'This command will associate your current nick with a lastfm username.', 1)

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

	def exec_command(self, message):
		try:
			command, arguments = self._parse_commands(message)
		except ValueError:
			return

		for cmd in self.commands:
			if command == cmd:
				return self._execute(command, arguments)
		raise ValueError('Unknown command %s' % command)

	def _execute(self, command, arguments):
		"""docstring for execute"""
		if len(arguments) < self.commands[command][1]:
			return "Not enough arguments!"

		do_cmd = 'do_'+command
		return getattr(self, do_cmd)(arguments)

	def do_help(self, arguments):
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

	def do_compare(self, arguments):
		"""Compare 2 lastfm users."""
		user1 = arguments[0]
		user2 = arguments[1]
		try:
			comparer = self.lastfm.get_user(user1)
			compare = comparer.compare_with_user(user2)
		except WSError as e:
			return(e.reason)
			return
		rating = int(compare[0])*100
		try:
			common_artists = ', '.join([artist.name for artist in compare[1]])
		except IndexError:
			common_artists = 'None!'

		return("Compatibility between %s and %s is %d%%! Common artists are: %s."\
					% (user1, user2, rating, common_artists))

	def do_np(self, arguments):
		"""Playing current or last playing song by the user."""
		user = self.lastfm.get_user(arguments[0])
		np = user.get_now_playing()
		if not np:
			last_song = user.get_recent_tracks(2)[0][0]
			return("%s last played: %s" % (user, last_song[0]))
		else:
			return("%s is playing: %s" % (user, np))

	def do_fm_register(self, arguments):
		"""Register a nick to a username."""
		return "This command is not implemented yet."

commands = user_commands()
commands.add_command(':np', ':np\nThis command will show the current song '\
		'playing in your lastfm profile', 1)
commands.add_command(':compare', ":compare `user1` `user2`\nThis command will "\
		"compare user1 to user2's lastfm profiles", 2)
commands.add_command(':fm_regiser', 'usage: :fm_register `lastfm username`\n'\
		'This command will associate your current nick with a lastfm username.')

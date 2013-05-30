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
import gentoobot.config

# Lastfm instance
# last_opt = gentoobot.config.get_conf('lastfm')
# lastfm = LastFMNetwork(api_key = last_opt['api_pub'], api_secret = last_opt['api_secret'])

class commands(object):
	"""docstring for command"""
	def __init__(self):
		self.parser = ArgumentParser(prefix_chars=':', add_help=False)
		self.commands = {}
		self.add_command(':help', 'help', 'show this help message')

	def add_command(self, command, method, help):
		"""docstring for add_command"""
		self.parser.add_argument(command, help=help, dest=method, nargs=REMAINDER)
		self.commands[method] = (command, help)

	def parse_commands(self, message):
		"""docstring for parse_commands"""
		cmds = vars(self.parser.parse_known_args(message.split())[0])
		for cmd in cmds:
			if not cmds[cmd] == None:
				return cmd, cmds[cmd]
		else: return None

	def do_command(self, message):
		"""docstring for do_command"""
		try:
			command, arguments = self.parse_commands(message)
		except ValueError:
			return
		except TypeError:
			return

		for method in self.commands:
			if command == method:
				return self.execute(method, arguments)
		raise ValueError('Unknown command %s' % command)

	def execute(self, method, arguments):
		"""docstring for execute"""
		try:
			return getattr(self, 'do_'+method)(arguments)
		except AttributeError:
			return 'No method defined for %s yet.' % method

	def do_compare(self, arguments):
		"""Compare 2 lastfm users."""
		if len(arguments) < 2:
			return 'Not enough arguments!'
		user1 = arguments[0]
		user2 = arguments[1]
		try:
			comparer = lastfm.get_user(user1)
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
					% (user1, user2, common_artists))

	def do_nowplaying(self, arguments):
		"""Playing current or last playing song by the user."""
		if not arguments:
			return "Not enough arguments!"

		user = lastfm.get_user(arguments[0])
		np = user.get_now_playing()
		if not np:
			last_song = user.get_recent_tracks(2)[0]
			return("%s last played: %s" % (user, last_song))
		else:
			return("%s is playing: %s" % (user, np))

	def do_help(self, arguments):
		"""docstring for do_help"""
		if not arguments:
			cmds = ', '.join([self.commands[cmd][0] for cmd in self.commands])
			return 'Available commands are: %s.' % cmds
		elif arguments[0].startswith(":"):
			return "Try without the : prefix you dumb cunt."
		else:
			command = arguments[0]
			for method in self.commands:
				cmd = self.commands[method][0][1:]
				if command == cmd:
					return self.commands[method][1]
			return "Command %s not found!" % command

commands = command()
commands.add_command(':np', 'nowplaying', 'Show the current playing song in lastfm')
commands.add_command(':compare', 'compare', 'Compare 2 lastfm profiles')

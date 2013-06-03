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

import re
from shlex import split
from urllib import urlencode, urlopen
from json import loads
from inspect import getargspec

from pylast import LastFMNetwork, WSError
from bs4 import BeautifulSoup

from gentoobot.config import get_config
from config import get_config, save_db, load_db

# Raised when you want to force a method to stop executing a command and print
# the output of this exception
class GottaGoFast(Exception): pass

class Commands():
	def __init__(self, last_pub, last_secret, prefix=':'):
		self.commands = self.get_commands()
		self.prefix = prefix

	def get_commands(self):
		"""Get a list of methods that stat with d_"""
		methods = [m for m in dir(self) if m.startswith('do_')]
		commands = {}

		for method in methods:

			callable = getattr(self, method)

			m = method[3:]
			help = callable.__doc__
			commands[m] = {"help":help, "nargs":0,
					"registered": False}

			a = getargspec(callable)
			try:
				defaults = dict(zip(a.args[-len(a.defaults):],a.defaults))
			except TypeError:
				continue
			if 'nargs' in defaults:
				commands[m]['nargs'] = defaults['nargs']
			if 'registered' in defaults:
				commands[m]['registered'] = defaults['registered']
		return commands

	def _parse_command(self, msg):
		"""Parse a message for commands."""
		if not msg.startswith(self.prefix):
			return None, None

		arguments = split(msg)
		cmd = arguments.pop(0)[1:]
		if cmd in self.commands:
			return cmd, arguments
		return None, None

	def _execute(self, command, user, arguments, bot):
		"""Execute the method associated with the command."""
		nargs = self.commands[command]['nargs']
		argslen = len(arguments)
		registered = self.commands[command]['registered']

		if registered and not self._is_registered(user, bot):
			return "You must be registered to use that command"

		if argslen < nargs:
			suffix = ''
			if nargs > 1:
				suffix = 's'
			return ":%s requires atleast %s argument%s!\nSee :help %s for more "\
					"information" % (command, nargs, suffix, command)

		method = 'do_'+command
		if not hasattr(self, method):
			return "Woops, it looks like %s is not yet implemented." % command
		return getattr(self, method)(user, arguments, bot)

	def run(self, bot, user, message):
		"""Parse the message, if a command is found then execute it."""
		command, arguments = self._parse_command(message)
		if command == arguments == None:
			return

		for cmd in self.commands:
			if command == cmd:
				try:
					reply = self._execute(command, user, arguments, bot)
					bot.tell(user, reply)
					return
				except GottaGoFast as e:
					bot.say("%s, %s" % (user.nick, str(e)))
					return

	def _is_registered(self, user, bot):
		"""Return True if a user is registered for his nick."""
		who = bot.who(user)
		if 'r' in who['flags']:
			return True
		return False

	def load_db(self, server, database):
		"""Save a database."""
		if not hasattr(self, database):
			setattr(self, database, load_db(server, database))
		return getattr(self, database)

	def update_db(self, server, database, value):
		"""Replace `database` by a new `value` and save the changes"""
		setattr(self, database, value)
		save_db(server, database, value)

	def do_help(self, user, arguments, bot):
		"""help [command]

		Display bot usage help.
		If [command] is specified then you will get help for that command."""

		if not arguments:
			cmds = ', '.join([self.prefix+cmd for cmd in self.commands])
			return "Available commands are %s.\nTry %shelp `command` for command "\
					'specific help.' % (cmds, self.prefix)
		else:
			cmd = arguments[0]
			for command in self.commands:
				if cmd in (command, self.prefix+command):

					help = self.commands[command]['help']
					help = re.sub(r'\t', '', re.sub(r'(\n)+', '\n', help))

					if self.commands[command]['registered']:
						help += "\nNote: You must be registered and logged in "\
							"to your irc nick to use this command."
					return "Usage: %s%s" % (self.prefix, help)
			return 'Unknown command "%s"' % cmd

class UserCommands(Commands):
	"""User commands."""
	def __init__(self, last_pub, last_secret, prefix=':'):
		Commands.__init__(self, last_pub, last_secret, prefix)
		self.lastfm=LastFMNetwork(api_key=last_pub, api_secret=last_secret)

	def do_g(self, user, arguments, bot, nargs=1):
		"""g `search query`

		Perform a google search query."""
		search = ' '.join(arguments)
		query = urlencode({'q':search})
		url = urlopen('http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s'\
				% query)
		response = loads(url.read())
		try:
			result = response['responseData']['results'][0]
		except (KeyError, IndexError):
			return 'No results found for "%s"' % (search)
		link = result['unescapedUrl']
		title = BeautifulSoup(result['title']).text
		content = BeautifulSoup(result['content']).text
		return "%s\n%s\n%s" % (link, title, content)

	def do_yt(self, user, arguments, bot, nargs=1):
		"""yt `search query`

		Perform a youtube search query."""
		search = ' '.join(arguments)
		query = urlencode({'q':search})
		url = urlopen('https://gdata.youtube.com/feeds/api/videos?alt=json&%s'\
				% query)
		response = loads(url.read())
		try:
			result = response['feed']['entry'][0]#['media$group']['media$player'][0]['url'].split('&', 1)[0]
		except (KeyError, IndexError):
			print('No results found!')
			return 'No results found for "%s"' % search
		link = result['media$group']['media$player'][0]['url'].split('&', 1)[0]
		title = result['title']['$t']
		return "%s\n%s" % (link, title)

	def _nick_to_lastfm(self, nick, bot):
		"""Take a nick string, return the lastfm username registered to it."""

		lastfm_users = self.load_db(bot.server, 'lastfm_users')
		if lastfm_users == None:
			lastfm_users = {}

		if nick.lower() in lastfm_users:
			user = lastfm_users[nick.lower()]
		else:
			user = nick

		user = self.lastfm.get_user(user)
		try:
			user.get_id()
		except WSError as e:
			raise GottaGoFast("Unknown name %s\nTry registering using fmregister"\
				" with a valid lastfm username." % str(user))
		return user

	def do_fmregister(self, user, arguments, bot, nargs=1, registered=True):
		"""fmregister `lastfm username`

		Associate your current nick with a lastfm username."""
		username = self.lastfm.get_user(arguments[0])
		try:
			username.get_id()
		except WSError as e:
			return str(e)

		username = str(username)
		lastfm_users = self.load_db(bot.server, 'lastfm_users')
		if lastfm_users == None:
			lastfm_users = {}
		lastfm_users[user.nick.lower()] = username
		self.update_db(bot.server, 'lastfm_users', lastfm_users)
		return "You have been associated with http://last.fm/user/%s" % username

	def _now_playing(self, user):
		"""Get the current playing song of a lastfm user"""
		try:
			np = user.get_now_playing()
		except IndexError:
			raise GottaGoFast("User %s has not scrobbled anything yet." % user)
		if not np:
			last_song = user.get_recent_tracks(2)[0][0]
			return "last played %s." % last_song
		else:
			return "are playing %s." % str(np)

	def do_np(self, user, arguments, bot):
		"""np [user]

		Show the song currently playing in your lasftm profile
		if [user] is specified, it will use that persons lastfm."""
		if len(arguments) > 0:
			nick = arguments[0]
			username = self._nick_to_lastfm(nick, bot)
			return "%s %s" % (nick, self._now_playing(username).replace(
											'are playing', 'is playing'))

		username = self._nick_to_lastfm(user.nick, bot)
		print('USERNAME IS '+str(username))
		return "You %s" % (self._now_playing(username))

	def do_compare(self, user, arguments, bot, nargs=1):
		"""compare `user` [user2]

		Compare your lasftm profile with `user`
		If [user2] is specified, i will compare him with `user` instead."""
		if not len(arguments) > 1:
			user1 = user.nick
			user2 = arguments[0]
			comparer = self._nick_to_lastfm(user1, bot)
			compared_to = self._nick_to_lastfm(user2, bot)
		else:
			user1 = arguments[0]
			user2 = arguments[1]
			comparer = self._nick_to_lastfm(user1, bot)
			compared_to = self._nick_to_lastfm(user2, bot)

		if comparer == compared_to:
			return "Try giving me different users smartass."

		diff = comparer.compare_with_user(compared_to)
		rating = float(diff[0])*100
		rating = int(rating)
		common_artists = diff[1]
		if common_artists:
			common_artists = ', '.join([artist.name for artist in diff[1]])
		else:
			common_artists = 'None!'
		return("Compatibility between %s and %s is %d%%!\nCommon artists are %s"\
					% (user1, user2, rating, common_artists))

	def do_whois(self, user, arguments, bot, nargs=1):
		"""whois `nick`

		Perform a whois query on `nick`
		Why would you want to use such a stupid command?"""
		who = bot.who(arguments[0])
		if who == 'REQUEST TIMEOUT':
			return "Even i don't know who the fuck %s is" % arguments[0]
		reply = ', '.join(["%s: %s" % (k, v) for k,v in who.items()])
		return reply

lastfm_conf = get_config('LASTFM')
user_commands = UserCommands(lastfm_conf['api_pub'], lastfm_conf['api_secret'])

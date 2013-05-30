#!/usr/bin/env python
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

import re, sys
from urllib.request import urlopen
from urllib.error import *
from html.parser import HTMLParser
from time import sleep
from argparse import ArgumentParser, REMAINDER

import pylast
import irc.bot

class GentooBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667, reconnect=5):
		server_conn = irc.bot.ServerSpec(server, port)
		irc.bot.SingleServerIRCBot.__init__(self, [server_conn], nickname, nickname,
				reconnection_interval=reconnect)
		self.channel = channel
		self.reconnect = reconnect
		self.nickname = nickname
		self.server = server
		self.port = port

		# User arguments.
		self.cmd = ArgumentParser(description="GentooBot is an annoying bot "\
				"designed to spam install gentoo on users, all other features "\
				"are simply there to keep people from ignoring the bot.\n"\
				"Made by axujen <https://github.com/axujen/gentoo-bot>",
				add_help=False, prefix_chars=":")
		self.cmd.add_argument(":np", ":nowplaying", metavar="user", dest="np",
				nargs=REMAINDER,
				help="display current or last played song by `user`.")
		self.cmd.add_argument(":compare", metavar="user1 user2", dest="compare",
				nargs=REMAINDER,
				help="compare `user1` and `user2` lastfm profiles.")

	def on_welcome(self, c, e):
		c.join(self.channel)
		self.say(c, "Ahoy! im back.")

	def on_pubmsg(self, c, e):
		self.installgentoo_reply(c, e)
		self.resolve_url(c, e)
		self.do_command(c, e)

	def on_kick(self, c, e):
		"""autorejoin when kicked."""
		sleep(self.reconnect)
		c.join(self.channel)

	def installgentoo_reply(self, c, e):
		msg = e.arguments[0]
		nick = e.source.split('!', 1)[0]
		ig_keywords = ('ubuntu', 'redhat', 'fedora', 'mint', 'debian',
				'windows', 'mac', 'arch', 'microsoft', 'apple', 'bsd', 'minix',
				'haiku', 'BeOS', 'TempleOS', 'OSX', 'Plan9', 'Unix', 'SparrowOS',
				'Wangblows', "linux", "lunix", "archlinux")
		for keyword in ig_keywords:
			# if keyword.lower() in msg.lower():
			if re.search(r"\b(%s)\b" % keyword, msg, re.I):
				self.say(c, "%s: Install Gentoo." % nick)
				break

	def resolve_url(self, c, e):
		"""if found, resolve the title of a url in the message."""
		msg = e.arguments[0]
		url_pattern = re.compile(r"https?:\/\/w{0,3}\w*?\.(\w*?\.)?\w{2,3}\S*|www\.(\w*?\.)?\w*?\.\w{2,3}\S*|(\w*?\.)?\w*?\.\w{2,3}[\/\?]\S*")
		if re.match(url_pattern, msg):
			url = re.match(url_pattern, msg).group(0)
			print('Found url! %s' % url)
			try:
				page = urlopen(url)
			except HTTPError as e:
				self.say(c, "HTTP Error %d" % e.code)
				return
			except URLError as e:
				self.say(c, "Failed to reach server, reason %s" % e.reason)
				return
			except ValueError:
				try:
					page = urlopen("http://%s" % url)
				except:
					return
			page_html = page.readall().decode()
			if re.findall(r"<title>(.*)</title>", page_html):
				title = HTMLParser().unescape(re.findall(r"<title>(.*)</title>", page_html)[0])
				self.say(c, "Page title: %s" % title)
				return
			self.say(c, "No title found for %s." % url)

	def do_command(self, c, e):
		"""Handler for user commands."""
		try:
			cmds = self.cmds.parse_args(e.arguments[0])
		except SystemExit: # SystemExit means no args we found.
			return
		if cmds.np:
			self.lastfm_np(c, cmds.np[0])
			return
		if cmds.compare:
			try:
				self.lastfm_compare(c, cmds.compare[0], cmds,compare[1])
				return
			except IndexError:
				self.say(c, "Not enough arguments!")
				return


	def lastfm_compare(self, c, user1, user2):
		"""Compare 2 lastfm users."""
		try:
			comparer = last.get_user(user1)
			compare = comparer.compare_with_user(user2)
		except WSError as e:
			self.say(c, e.reason)
			return
		rating = int(compare[0])*100
		try:
			common_artists = ', '.join([artist.name for artist in compare[1]])
		except IndexError:
			common_artists = 'None!'

		self.say(c, "Compatibility between %s and %s is %d%%! Common artists are: %s."\
					% (user1, user2, common_artists))

	def lastfm_np(self, c, user):
		"""Playing current or last playing song by the user."""
		user = last.get_user(user)
		np = user.get_now_playing()
		if not np:
			last_song = user.get_recent_tracks(2)[0]
			self.say(c, "%s last played: %s" % (user, last_song))
		else:
			self.say(c, "%s is playing: %s" % (user, np))

	def say(self, c, message):
		"""Print message in the channel"""
		c.privmsg(self.channel, message)

arguments = ArgumentParser()
arguments.add_argument('-s', '--server', default='irc.installgentoo.com',
		help='irc server to connect to.', metavar='server', dest='server')
arguments.add_argument('-p', '--port', default=6667, help='server port.',
		dest='port', metavar='port')
arguments.add_argument('-n', '--nick', default='GentooTestBot', help="bot's name.",
		dest='nick', metavar='nick')
arguments.add_argument('-c', '--channel', default='#/g/test', metavar='channel',
		help='channel to connect to.', dest='channel')

def main():
	args = arguments.parse_args()

	import gentoobot.config
	lastfm = gentoobot.config.lastfm
	last = pylast.LastFMNetwork(api_key = lastfm['api_pub'],
			api_secret = lastfm['api_secret'])

	Gentoo_Bot = GentooBot(args.channel, args.nick, server=args.server, port=args.port)

	try:
		Gentoo_Bot.start()
	except Exception as e:
		# Log errors.
		with open('/tmp/gentoobot_error.log', 'a') as error_log:
			e_name = re.findall(r"<class '(.*)'>", str(e.__class__))[0]
			e_len = len(e_name)
			error_log.write('-'*e_len)
			error_log.write(e_name)
			error_log.write('-'*e_name)
			error_log.write(sys.exc_info()[2])
		sys.exit()

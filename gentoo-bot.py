#!/usr/bin/env python
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
from urllib.request import urlopen
from urllib.error import *
from html.parser import HTMLParser
from time import sleep
from argparse import ArgumentParser

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

	def on_welcome(self, c, e):
		"""docstring for on_welcome"""
		c.join(self.channel)

	def on_pubmsg(self, c, e):
		"""docstring for on_pubmsg"""
		self.installgentoo_reply(c, e)
		self.resolve_url(c, e)
		self.last_fm(c, e)

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

	def last_fm(self, c, e):
		"""Last fm commands"""
		msg = e.arguments[0]
		if not msg.startswith(":"):
			return
		if msg.startswith(":compare "):
			args = msg.split()[1:]
			try:
				first_user = last.get_user(args[0])
				compare = first_user.compare_with_user(args[1])
				rating = int(float(compare[0])*100)
			except pylast.WSError as e:
				self.say(c, e.details)
				return
			except IndexError:
				self.say(c, "Not enough arguments!")
			try:
				common_artists = compare[1]
			except IndexError:
				common_artists = None
				return
			if common_artists:
				n = 0
				artists = []
				for artist in common_artists:
					if n >= 4:
						break
					n += 1
					artists.append(artist.name)
				self.say(c, "Compatibility with %s and %s is %d%%. Common artists include: %s" % (args[0], args[1], rating, ', '.join(artists)))
			else:
				self.say(c, "Compatibility with %s and %s is %d%%." %  (args[0], args[1], rating))
		elif msg.startswith(":np "):
			try:
				user = msg.split()[1]
			except IndexError:
				user = e.source.split('!', 1)[0]
			user = last.get_user(user)
			last_song = user.get_now_playing()
			if not last_song:
				last_song = user.get_recent_tracks(2)[0]
				# need to to give a different message.
			self.say(c, "%s now playing: %s by %s from %s" % (user,
				last_song.title, last_song.artist.name, last_song.get_album().title))

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

if __name__ == '__main__':
	args = arguments.parse_args()
	with open("last.fm", 'rt') as f:
		api_pub = f.readline()[:-1]
		api_secret = f.readline()[:-1]
	last = pylast.LastFMNetwork(api_key = api_pub, api_secret = api_secret)
	Gentoo_Bot = GentooBot(args.channel, args.nick, server=args.server, port=args.port)
	Gentoo_Bot.start()

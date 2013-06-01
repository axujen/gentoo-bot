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
from urllib.parse import urlparse
from urllib.error import *
from bs4 import BeautifulSoup
from time import sleep
from random import choice
from json import loads
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import irc.bot

from gentoobot.commands import commands
import gentoobot.config as config

class GentooBot(irc.bot.SingleServerIRCBot):
	def __init__(self):
		self.banned_words = ('facebook', 'kek', 'reddit', 'kex')
		self.greetings = ('Hello %s!', 'Welcome %s!', 'Everybody rejoice! %s is here!')
		self.ig_replies = (
		'Install Gentoo.', 'You know what you should do? you should install gentoo.',
		'Have you ever heard of this os? its called gentoo and i think you should install it.',
		'Gentoo, install it motherfucker.')
		self.ig_keywords = ('ubuntu', 'redhat', 'fedora', 'mint', 'debian', 'hurd',
			'windows', 'mac', 'arch', 'microsoft', 'apple', 'minix',
			'haiku', 'BeOS', 'TempleOS', 'OSX', 'Plan9', 'Unix', 'SparrowOS',
			'Wangblows', "linux", "lunix", "archlinux", 'macs', 'os x')
		self.wholist = {}

	def on_welcome(self, c, e):
		c.join(self.channel)

	def on_pubmsg(self, c, e):
		self.installgentoo_reply(c, e)
		self.bsd_is_dum(c, e)
		self.resolve_url(c, e)
		self.do_command(c, e)

	def on_whoreply(self, c, e):
		"""docstring for on_whoreply"""
		args = e.arguments
		fields = ('channel', 'realname', 'host', 'server', 'nick', 'flags', 'tail')
		who = {}
		for item, field in zip(args, fields):
			who[field] = item
		print(who)
		self.wholist[who['nick'].lower()] = who

	def on_kick(self, c, e):
		"""autorejoin when kicked."""
		sleep(self.reconnect)
		c.join(self.channel)

	def on_join(self, c, e):
		"""docstring for on_join"""
		# self.greeting(c, e)

	def who(self, nick):
		"""Perform a WHO command on `nick`"""
		self.connection.who(nick)

	def installgentoo_reply(self, c, e):
		msg = e.arguments[0]
		nick = e.source.nick

		for keyword in self.ig_keywords:
			if re.search(r"\b(%s)\b" % keyword, msg, re.I):
				reply = choice(self.ig_replies)
				self.say( "%s: %s" % (nick, reply))
				return

	def bsd_is_dum(self, c, e):
		"""docstring for bsd_is_dum"""
		if re.search(r'(^|[^\d.-])bsd\b', e.arguments[0], re.I):
			self.say( '%s: bsd is dum' % e.source.nick)

	def resolve_url(self, c, e):
		"""if found, resolve the title of a url in the message."""
		msg = e.arguments[0]
		url_pattern = re.compile(r"\(?\bhttp[s]?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]")
		if re.search(url_pattern, msg):
			url = re.findall(url_pattern, msg)[0]
			print('Found url: %s' % url)
			try:
				o_url = urlopen(url)
			except (HTTPError, URLError) as e:
				self.say(str(e))
				return
			except ValueError:
				try:
					o_url = urlopen("http://%s" % url)
				except:
					return

			p_url = urlparse(url)
			if p_url.netloc == 'boards.4chan.org' and re.match(r'^/\w+/res/(\d+|\d+#p\d+)$', p_url.path):
				print('Is 4chan thread')
				path = p_url.path.split('/')
				board = path[1]
				thread = path[-1]

				try:
					op = loads(urlopen('https://api.4chan.org/%s/res/%s.json' %\
						(board, thread)).read().decode())['posts'][0]
				except (HTTPError, URLError):
					self.say(str(e))
					return

				comment = subject = None
				replies, images = op['replies'], op['images']

				if 'com' in op:
					comment = BeautifulSoup(op['com']).text
					if len(comment) > 100: comment = comment[:100]+'...'
				if 'sub' in op: subject = op['sub']

				message = 'Board: /%s/ | R: %s, I: %s | Subject: %s | Comment: %s'\
						% (board, replies, images, str(subject), str(comment))

				self.say(message)
				return

			soup = BeautifulSoup(o_url.read())
			if soup.title:
				title = soup.title.string
				self.say( "Page title: %s" % title)
				return

	def do_command(self, c, e):
		"""Handler for user commands."""
		if not e.arguments[0].startswith(":"):
			return

		msg = commands.exec_command(e)
		if isinstance(msg, str):
			self.say( msg)

	def say(self, message):
		"""Print message in the channel"""
		for word in self.banned_words:
			if word.lower() in message.lower():
				message = re.sub('(?i)'+word, '*'*len(word), message)

		message = re.sub(r'\n', '  |  ', message)
		self.connection.privmsg(self.channel, message)

	def greeting(self, c, e):
		"""docstring for greeting"""
		nick = e.source.nick
		if nick == self.nickname:
			return

		print('Greeting %s' % nick)
		greeting = choice(self.greetings)
		self.say(greeting % nick)

	def start(self, channel, nickname, server, port, reconnect=5):
		"""Start the bot."""
		server_spec = irc.bot.ServerSpec(server, port)
		self.channel = channel
		self.reconnect = reconnect
		self.nickname = nickname
		self.server = server
		self.port = port
		super().__init__([server_spec], nickname, nickname, reconnection_interval=reconnect)
		super().start()

GBot = GentooBot()

def main():
	# Get connection options written in config file.
	opt = config.get_conf('connection')
	# command line args
	arguments = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
	arguments.add_argument('-s', '--server', default=opt['server'],
			help='irc server to connect to.', metavar='server', dest='server')
	arguments.add_argument('-p', '--port', default=opt['port'], dest='port',
			help='server port.', metavar='port')
	arguments.add_argument('-n', '--nick', default=opt['nick'], dest='nick',
			help="bot's name.", metavar='nick')
	arguments.add_argument('-c', '--channel', default=opt['channel'],
			metavar='channel',	help='channel to connect to.', dest='channel')
	args = arguments.parse_args()

	print('Starting GentooBot in channel "%s" server "%s:%s", as "%s"' % ( args.channel,
		args.server, args.port, args.nick))
	try:
		GBot.start(args.channel, args.nick, server=args.server, port=int(args.port))
	except UnicodeDecodeError as e:
		GBot.say(e)
		print(e)

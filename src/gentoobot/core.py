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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re, sys, random, json, time
from urllib2 import urlopen, HTTPError
from urlparse import urlparse

from bs4 import BeautifulSoup
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from thread import start_new_thread

import irc.bot
from irc.client import NickMask

from gentoobot.commands import commands
from gentoobot.config import get_config, load_db

class GentooBotFrame(irc.bot.SingleServerIRCBot):
	"""Bot framework"""

	def __init__(self, server, port, channel, nick, reconnect=5):
		server_spec = irc.bot.ServerSpec(server, int(port))
		super(GentooBotFrame, self).__init__([server_spec], nick, nick, reconnection_interval=reconnect)

		self.reconnect = 5
		self.channel = channel
		self.nick = nick
		self.server = server
		self.port = int(port)

		self.wholist = {}

	def on_welcome(self, c, e):
		print('Joining %s' % self.channel)
		c.join(self.channel)

	def on_pubmsg(self, c, e):
		channel = e.target
		user = e.source
		message = e.arguments[0]
		print('[%s]%s| %s' % (channel, user.nick, message))
		self.actions(channel, user, message)

	def on_whoreply(self, c, e):
		args = e.arguments
		fields = ('channel', 'realname', 'host', 'server', 'nick', 'flags', 'tail')
		who = {}

		for item, field in zip(args, fields):
			if field == 'tail':
				continue
			who[field] = item

		self.wholist[who['nick'].lower()] = who
		self.whostatus = 'ACK'

	def on_kick(self, c, e):
		"""autorejoin when kicked."""
		time.sleep(self.reconnect)
		print('Rejoining %' % self.channel)
		c.join(self.channel)

	def who(self, nick, timeout = 5):
		"""Perform a WHO command on `nick`"""
		if isinstance(nick, NickMask):
			nick = nick.nick
		self.whostatus = 'REQUEST'
		self.connection.who(nick)
		n = 0

		while not self.whostatus == 'ACK':
			if n >= timeout:
				return "REQUEST TIMEOUT"
			n += 1
			time.sleep(2)

		return self.wholist[nick.lower()]

	def say(self, message):
		"""Print message in the channel"""
		message = re.sub(r'\n', ' | ', message)
		print('->[%s] %s' % (self.channel, message))
		self.connection.privmsg(self.channel, message)

	def tell(self, user, message):
		"""Tell a user a message"""

		if isinstance(user, NickMask):
			user = user.nick

		self.say("%s, %s" % (user, message))

class GentooBot(GentooBotFrame):
	"""The actual bot"""
	def __init__(self, server, port, channel, nick, reconnect=5):
		super(GentooBot, self).__init__(server, port, channel, nick, reconnect)

		self.admins = load_db(server, "admins")
		self.banned_words = load_db(server, 'banned_words')
		self.ig_keywords = load_db(server, 'ig_keywords')
		if self.ig_keywords == None:
			self.ig_keywords = [None]

		self.greetings = ('Hello %s!', 'Welcome %s!', 'Everybody rejoice! %s is here!')
		self.ig_replies = (
		'Install Gentoo.', 'You know what you should do? you should install gentoo.',
		'Have you ever heard of this os? its called gentoo and i think you should install it.',
		'Gentoo, install it motherfucker.')

		self.url_pattern = re.compile(r"((?:https?\:\/\/|www\.)(?:[-a-z0-9]+\.)*[-a-z0-9]+.*)")

	def actions(self, channel, user, message):
		start_new_thread(commands.run, (self, user, message))
		start_new_thread(self.url_title, (message,))
		self.installgentoo_reply(user, message)
		self.bsd_is_dum(user, message)

	def installgentoo_reply(self, user, message):
		if self.ig_keywords:
			for keyword in self.ig_keywords:
				if re.search(r"\b(%s)\b" % keyword, message, re.I):
					reply = random.choice(self.ig_replies)
					self.tell(user, reply)

	def bsd_is_dum(self, user, message):
		if re.search(r'(^|[^\d.-])bsd\b', message, re.I):
			self.tell(user, 'BSD is dum.')

	def url_title(self, msg):
		"""if found, resolve the title of a url in the message."""
		url_pattern = self.url_pattern
		if re.search(url_pattern, msg):
			url = re.findall(url_pattern, msg)[0]
			print('Detected url %s' % url)
			p_url = urlparse(url)
			if p_url.netloc == 'boards.4chan.org' and re.match(r'^/\w+/res/(\d+|\d+#p\d+)$', p_url.path):
				print('Is 4chan thread')
				path = p_url.path.split('/')
				board = path[1]
				thread = path[-1]
				op = json.loads(urlopen('https://api.4chan.org/%s/res/%s.json' %\
					(board, thread)).read().decode())['posts'][0]
				comment = subject = None
				replies, images = op['replies'], op['images']

				if 'com' in op:
					comment = BeautifulSoup(op['com']).text
					if len(comment) > 100: comment = comment[:100]+'...'
				if 'sub' in op: subject = op['sub']

				message = 'Board: /%s/ | R: %s, I: %s | Subject: %s | Comment: %s'\
						% (board, replies, images, str(subject), str(comment))

				return self.say(message)

			soup = BeautifulSoup(urlopen(url))
			if soup.title:
				title = soup.title.string
				return self.say( "Page title: %s" % title)

def main():
	opt = get_config('CONNECTION')
	bot = GentooBot(opt['server'],opt['port'],opt['channel'],opt['nick'])
	print('Connecting %s to %s in %s' % (opt['nick'],opt['channel'],opt['server']))
	bot.start()

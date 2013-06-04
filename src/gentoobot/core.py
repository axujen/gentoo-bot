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

from gentoobot.config import get_config, load_db
from gentoobot.commands import commands
from logger import log

class GentooBotFrame(irc.bot.SingleServerIRCBot):
	"""Bot framework"""

	def __init__(self, server, port, channel, nick, reconnect, verbose):
		server_spec = irc.bot.ServerSpec(server, int(port))
		super(GentooBotFrame, self).__init__([server_spec], nick, nick, reconnection_interval=reconnect)

		self.verbose = verbose
		self.reconnect = reconnect
		self.channel = channel
		self.nick = nick
		self.server = server
		self.port = int(port)

		self.wholist = {}

	def on_welcome(self, c, e):
		self.event_logger(e)
		print('Joining %s' % self.channel)
		c.join(self.channel)

	def on_pubmsg(self, c, e):
		self.event_logger(e)
		channel = e.target
		user = e.source
		message = e.arguments[0]

	def on_privmsg(self, c, e):
		"""docstring for on_privmsg"""
		self.event_logger(e)

	def on_action(self, c, e):
		"""docstring for on_action"""
		self.event_logger(e)

	def on_join(self, c, e):
		"""docstring for on_join"""
		self.event_logger(e)

	def on_part(self, c, e):
		"""docstring for on_part"""
		self.event_logger(e)

	def on_privnotice(self, c, e):
		"""docstring for on_privnotice"""
		self.event_logger(e)

	def on_pubnotice(self, c, e):
		"""docstring for on_pubnotice"""
		self.event_logger(e)

	def on_quit(self, c, e):
		"""docstring for on_quit"""
		self.event_logger(e)

	def on_nick(self, c, e):
		"""docstring for on_nick"""
		self.event_logger(e)

	def on_topic(self, c, e):
		"""docstring for on_topci"""
		self.event_logger(e)

	def on_mode(self, c, e):
		"""docstring for on_mode"""
		self.event_logger(e)

	def on_kick(self, c, e):
		"""autorejoin when kicked."""
		self.event_logger(e)
		time.sleep(self.reconnect)
		print('Rejoining %s' % self.channel)
		c.join(self.channel)

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

	def event_logger(self, event):
		pass

	def who(self, nick, timeout=5):
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
	def __init__(self, server, port, channel, nick, reconnect=5, verbose=False):
		super(GentooBot, self).__init__(server, port, channel, nick, reconnect, verbose)

		self.admins = load_db(server, "admins")
		self.banned_words = load_db(server, 'banned_words')
		self.ig_keywords = load_db(server, 'ig_keywords')
		if self.ig_keywords == None:
			self.ig_keywords = [None]

		self.replies = self._get_replies()
		self.greetings = ('Hello %s!', 'Welcome %s!', 'Everybody rejoice! %s is here!')
		self.ig_replies = (
		'Install Gentoo.', 'You know what you should do? you should install gentoo.',
		'Have you ever heard of this os? its called gentoo and i think you should install it.',
		'Gentoo, install it motherfucker.')

		self.url_pattern = re.compile(r"(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")

	def event_logger(self, event):
		"""Log an event"""
		try:
			log(self.server, event, self.verbose)
		except:
			pass

	def actions(self, channel, user, message):
		start_new_thread(commands.run, (self, user, message))
		try:
			self.url_title(message)
			self.reply(user, message)
		except:
			pass

	def url_title(self, msg):
		"""if found, resolve the title of a url in the message."""
		url_pattern = self.url_pattern
		if re.search(url_pattern, msg):
			url = re.findall(url_pattern, msg)[0][0]
			if url.startswith('www.'):
				url = 'http://'+url
			print('Detected url %s' % str(url))
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

	def reply(self, user, message):
		"""Reply to something"""
		for reply in self.replies:
			msg = getattr(self, reply)(message)
			if isinstance(msg, str):
				return self.tell(user, msg)

	def _get_replies(self):
		return sorted([reply for reply in dir(self) if reply.startswith('reply_')])

	def reply_1_installgentoo(self, message):
		if self.ig_keywords:
			for keyword in self.ig_keywords:
				if re.search(r"\b(%s)\b" % keyword, message, re.I):
					reply = random.choice(self.ig_replies)
					return reply

	def reply_2_bsd(self, message):
		if re.search(r'(^|[^\d.-])bsd\b', message, re.I):
			return "BSD is dum."

	def reply_3_implying(self, message):
		"""implying implications"""
		if message.startswith(('implying', '>implying')):
			return 'Implying implications.'

def main():
	opt = get_config('CONNECTION')
	misc = get_config('MISC')
	bot = GentooBot(opt['server'],opt['port'],opt['channel'],opt['nick'],
			reconnect=misc['reconnect'], verbose=misc['verbose'])
	print('Connecting %s to %s in %s' % (opt['nick'],opt['channel'],opt['server']))
	bot.start()

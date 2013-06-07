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

import re, sys, random, json, time, os
from urllib2 import urlopen, HTTPError
from urlparse import urlparse
from time import time, sleep
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from thread import start_new_thread
from signal import signal, SIGINT

import requests
import chardet
from bs4 import BeautifulSoup
import irc.bot
from irc.client import NickMask, Event

from gentoobot import logger
from gentoobot.config import get_config, load_db, config_base
from gentoobot.commands import commands
from gentoobot.brain import Brain

def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fT' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size

# Because fuck codecs
import codecs
def strict_handler(exception):
	return codecs.replace_errors(exception)
codecs.register_error("strict", strict_handler)

class GentooBotFrame(irc.bot.SingleServerIRCBot):
	"""Bot framework"""

	def __init__(self, server, port, channel, nick, password, reconnect):
		server_spec = irc.bot.ServerSpec(server, int(port))
		super(GentooBotFrame, self).__init__([server_spec], nick, nick, reconnection_interval=reconnect)

		self.reconnect = reconnect
		self.chans = [channel]
		self.nick = nick

		# This is the bots original nick, used for ghosting.
		self.my_nick = nick
		self.server = server
		self.port = int(port)
		self.password = password

		self.wholist = {}
		self.brain = Brain(os.path.join(config_base, 'brain.txt'))

	def on_welcome(self, c, e):
		logger.log_event(self.server, e)

		if self.password:
			self._identify()

		for channel in self.chans:
			self.join(channel)

	def _identify(self):
		"""Identify the bot"""
		self.connection.privmsg('nickserv', 'identify %s' % self.password)

	def on_pubmsg(self, c, e):
		logger.log_event(self.server, e)
		channel = e.target
		user = e.source
		message = e.arguments[0]
		try:
			self.actions(channel, user, message)
		except Exception as e:
			logger.error_log(e)

	def on_privmsg(self, c, e):
		logger.log_event(self.server, e)
		user = e.source
		msg = e.arguments[0]
		self.private_actions(user, msg)

	def actions(self, channel, user, message):
		pass

	def private_actions(self, user, msg):
		pass

	def on_action(self, c, e):
		"""docstring for on_action"""
		logger.log_event(self.server, e)

	def on_join(self, c, e):
		"""docstring for on_join"""
		logger.log_event(self.server, e)

	def on_part(self, c, e):
		"""docstring for on_part"""
		logger.log_event(self.server, e)

	def on_privnotice(self, c, e):
		"""docstring for on_privnotice"""
		logger.log_event(self.server, e)

	def on_pubnotice(self, c, e):
		logger.log_event(self.server, e)

	def on_quit(self, c, e):
		"""docstring for on_quit"""
		logger.log_event(self.server, e)

	def on_nick(self, c, e):
		"""docstring for on_nick"""
		logger.log_event(self.server, e)

	def on_topic(self, c, e):
		"""docstring for on_topci"""
		logger.log_event(self.server, e)

	def on_mode(self, c, e):
		"""docstring for on_mode"""
		logger.log_event(self.server, e)

	def on_kick(self, c, e):
		"""autorejoin when kicked."""
		logger.log_event(self.server, e)
		sleep(self.reconnect)
		self.join(e.target)

	def join(self, channel):
		logger.logger.warning('Joining %s', channel)
		self.connection.join(channel)

		if not channel in self.chans:
			self.chans.append(channel)

	def part(self, channel):
		"""Leave a channel"""
		logger.logger.warning('Leaving %s', channel)
		self.connection.part(channel)

		if channel in self.chans:
			self.chans.remove(channel)

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

	def on_nicknameinuse(self, c, e):
		self.nick += '_'
		c.nick(self.nick)

		if self.password:
			self.connection.privmsg('nickserv', 'ghost %s %s' % (self.my_nick, self.password))
			self.connection.nick(self.my_nick)
			self.nick = self.my_nick[:]
			self._identify()

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
			sleep(1)

		return self.wholist[nick.lower()]

	def say(self, channel, message):
		"""Send a message to the channel"""

		if isinstance(message, str):
			guess = chardet.detect(message)['encoding']
			message = message.decode(guess, errors='replace')

		message = re.sub(r'\n', ' | ', message)

		# 2 thirds of it is real
		source = NickMask('%s!%s@%s' % (self.nick, self.nick, self.nick))
		target = channel
		arguments = [message]
		if target.startswith('#'):
			type = 'pubmsg'
		else:
			type = 'privmsg'
		e = Event(type, source, target, arguments)

		self.connection.privmsg(channel, message)
		logger.log_event(self.server, e)

	def tell(self, channel, user, message):
		"""Tell a user a message"""

		if isinstance(user, NickMask):
			user = user.nick

		self.say(channel, "%s, %s" % (user, message))

	def quit(self, *args):
		"""Disconnect and save the brain"""
		self.disconnect('Bye Bye')
		logger.logger.warning("Disconnected from the server!")
		self.brain.save_brain()
		raise SystemExit

class GentooBot(GentooBotFrame):
	"""The actual bot"""
	def __init__(self, server, port, channel, nick, password=None,
			reconnect=5):
		super(GentooBot, self).__init__(server, port, channel, nick, password,
				reconnect)

		self.admins = load_db(server, "admins")
		self.banned_words = load_db(server, 'banned_words')
		self.ig_keywords = load_db(server, 'ig_keywords')
		if self.ig_keywords == None:
			self.ig_keywords = [None]

		self.chattiness = 3
		self.replies = self._get_replies()
		self.treplies = self._get_treplies()
		self.last_reply = 0
		self.greetings = ('Hello %s!', 'Welcome %s!', 'Everybody rejoice! %s is here!')
		self.ig_replies = (
		'Install Gentoo.', 'You know what you should do? you should install gentoo.',
		'Have you ever heard of this os? its called gentoo and i think you should install it.',
		'Gentoo, install it motherfucker.')

		self.url_pattern = re.compile(r"(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")
		self.smiley_pattern = re.compile(r"([:x=;]{1,2}(?:\)|D|P|O|o))(?:\s|$)", re.I)

	def actions(self, channel, user, message):
		try:
			self.brain.process_line(message)
			start_new_thread(commands.run, (self, channel, user, message))
			self.reply(channel, user, message)
		except Exception as e:
			logger.error_log(e, self.server)

	def private_actions(self, user, message):
		try:
			start_new_thread(commands.run, (self, user.nick, user, message))
		except Exception as e:
			logger.error_log(e)

	def reply(self, channel, user, message):
		"""Reply to something"""
		for reply in self.replies:
			status = getattr(self, reply)(channel, user, message)
			if status == True: return

		curtime = int(time())
		for treply in self.treplies:
			if not curtime >= self.last_reply+20:
				logger.logger.warning('Timed reply cooldown left %d', self.last_reply+20-curtime)
				return
			status = getattr(self, treply)(channel, user, message)
			if status == True:
				self.last_reply = curtime
				return

	def _get_replies(self):
		return sorted([reply for reply in dir(self) if reply.startswith('reply_')])

	def _get_treplies(self):
		return sorted([reply for reply in dir(self) if reply.startswith('treply_')])

	def _4chan_title(self, path):
		path = path.split('/')
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

		return message

	def reply_1_url_title(self, channel, user, msg):
		"""if found, resolve the title of a url in the message."""
		if re.search(self.url_pattern, msg):
			url = re.findall(self.url_pattern, msg)[0][0]

			if url.startswith('www.'):
				url = 'http://'+url

			logger.logger.warning('Detected url %s' % str(url))
			headers = requests.get(url).headers
			if not 'text/html' in headers['content-type']:
				self.say(channel, '[URI] `%s` %s'\
						% (headers['content-type'],
							convert_bytes(headers['content-length'])))
				return

			p_url = urlparse(url)
			if p_url.netloc == 'boards.4chan.org' and re.match(r'^/\w+/res/(\d+|\d+#p\d+)$', p_url.path):
				logger.logger.warning('%s is a 4chan thread' % (url))
				self.say(channel, self._4chan_title(p_url.path))
				return

			data = urlopen(url).read()
			soup = BeautifulSoup(data)
			if soup.title:
				title = soup.title.string
				self.say(channel, "[URI] %s" % title)
				return True

	def reply_2_brain(self, channel, user, msg):
		"""Reply with a randomly generated sentence based on ``msg`"""
		if msg.startswith(self.nick):
			msg = ' '.join(msg.split()[1:])
			self.tell(channel, user, self.brain.generate_sentence(msg))
			return True
		elif re.search(r'\b%s\b' % self.nick, msg):
			self.say(channel, self.brain.generate_sentence(msg))
			return True
		elif random.randint(0, 100) < self.chattiness:
			self.say(channel, self.brain.generate_sentence(msg))
			return True
		return

	def treply_1_installgentoo(self, channel, user, msg):
		if self.ig_keywords:
			for keyword in self.ig_keywords:
				if re.search(r"\b(%s)\b" % keyword, msg, re.I):
					reply = random.choice(self.ig_replies)
					self.tell(channel, user, reply)
					return True

	def treply_2_bsd(self, channel, user, msg):
		if re.search(r'(^|[^\d.-])bsd\b', msg, re.I):
			self.tell(channel, user, 'bsd is dum.')
			return True

	def treply_3_implying(self, channel, user, msg):
		"""implying implications"""
		if msg.startswith(('implying', '>implying')):
			self.tell(channel, user, 'Implying implications')
			return True

	def treply_4_smiley(self, channel, user, msg):
		smileys = re.findall(self.smiley_pattern, msg)
		if smileys:
			logger.logger.warning('Found %s in %s', ', '.join(smileys), msg)
			choice = random.choice(smileys)
			logger.logger.warning('replying with %s', choice)
			self.tell(channel, user, choice)
			return True

def main():
	opt = get_config('CONNECTION')
	misc = get_config('MISC')
	bot = GentooBot(opt['server'],opt['port'],opt['channel'],opt['nick'],
			password=opt['password'], reconnect=int(misc['reconnect']))
	logger.logger.warning('Connecting %s to %s in %s' % (opt['nick'],opt['channel'],opt['server']))

	signal(SIGINT, bot.quit)
	try:
		bot.start()
	except Exception as e:
		logger.error_log(exception)
		bot.quit()

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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.	If not, see <http://www.gnu.org/licenses/>.

import re, random, json
from urllib2 import urlopen, Request
from urlparse import urlparse
from time import time, sleep
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from thread import start_new_thread
from signal import signal, SIGINT

from bs4 import BeautifulSoup
import irc.bot
from irc.client import NickMask, Event

from gentoobot import logger
from gentoobot.config import get_config, load_db, config_base
from gentoobot.commands import commands

# Replace characters when unable to decode them properly
import codecs
def strict_handler(exception):
	return codecs.replace_errors(exception)
codecs.register_error("strict", strict_handler)

class GentooBot(irc.bot.SingleServerIRCBot):
	"""Bot framework"""

	def __init__(self, server, port, channel, nick, password=None, reconnect=5):
		server_spec = irc.bot.ServerSpec(server, int(port))
		super(GentooBot, self).__init__([server_spec], nick, nick, reconnection_interval=reconnect)
		options = get_config('OPTIONS')

		self.reconnect = reconnect
		self.chans = [channel]
		self.chattiness = options['chattiness']
		self.admins = load_db(server, "admins")

		# This is the bots original nick, used for ghosting.
		self.my_nick = nick
		self.nick = nick
		self.server = server
		self.port = int(port)
		self.password = password

		self.wholist = {}
		self.replies = self._get_replies()
		self.timed_replies = self._get_timed_replies()
		self.last_reply = 0

		self.url_pattern = re.compile(r"(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")
		self.smiley_pattern = re.compile(r"([:x=;]{1,2}(?:\)|D|P|O|o))(?:\s|$)", re.I)

	def on_welcome(self, c, e):
		logger.log_event(self.server, e)

		if self.password:
			self._identify()

		for channel in self.chans:
			self.join(channel)

	def on_pubmsg(self, c, e):
		logger.log_event(self.server, e)
		channel = e.target
		user = e.source
		message = e.arguments[0]
		self.pub_commands(channel, user, message)

	def on_privmsg(self, c, e):
		logger.log_event(self.server, e)
		user = e.source
		msg = e.arguments[0]
		self.priv_commands(user, msg)

	def pub_commands(self, channel, user, message):
		start_new_thread(commands.run, (self, channel, user, message))
		self.reply(channel, user, message)

	def priv_commands(self, user, message):
		"""What to do when receiving commands in privmsg"""
		start_new_thread(commands.run, (self, user.nick, user, message))

	def on_kick(self, c, e):
		logger.log_event(self.server, e)
		sleep(self.reconnect)
		self.join(e.target)

	def join(self, channel):
		logger.logger.warning('Joining %s', channel)
		self.connection.join(channel)

		if not channel in self.chans:
			self.chans.append(channel)

	def part(self, channel):
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

	def who(self, nick, timeout=5):
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
		if isinstance(message, str):
			message = message.decode('utf-8', errors='replace')

		message = re.sub(r'\n', ' | ', message)

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
		if isinstance(user, NickMask):
			user = user.nick

		self.say(channel, "%s, %s" % (user, message))

	def reply(self, channel, user, message):
		"""Reply to someone"""
		for reply in self.replies:
			status = getattr(self, reply)(channel, user, message)
			if status == True: return

		curtime = int(time())
		for treply in self.timed_replies:
			if not curtime >= self.last_reply+self.chattiness:
				logger.logger.warning('Timed reply cooldown left %d', self.last_reply+self.chattiness-curtime)
				return
			status = getattr(self, treply)(channel, user, message)
			if status == True:
				self.last_reply = curtime
				return

	def quit(self, *args):
		self.disconnect('Bye Bye')
		logger.logger.warning("Disconnected from the server!")
		raise SystemExit

	def _get_replies(self):
		return sorted([reply for reply in dir(self) if reply.startswith('reply_')])

	def _get_timed_replies(self):
		return sorted([reply for reply in dir(self) if reply.startswith('timed_reply_')])

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

	def reply_url_title(self, channel, user, msg):
		"""if found, resolve the title of a url in the message."""
		if re.search(self.url_pattern, msg):
			url = re.findall(self.url_pattern, msg)[0][0]

			if url.startswith('www.'):
				url = 'http://'+url

			logger.logger.warning('Detected url %s' % str(url))
			headers = urlopen(HeadRequest(url)).headers.dict
			if not 'text/html' in headers['content-type']:
				self.say(channel, '[URI] `%s` %s' % (headers['content-type'],
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

	def timed_reply_smiley(self, channel, user, msg):
		smileys = re.findall(self.smiley_pattern, msg)
		if smileys:
			logger.logger.warning('Found %s in %s', ', '.join(smileys), msg)
			choice = random.choice(smileys)
			logger.logger.warning('replying with %s', choice)
			self.tell(channel, user, choice)
			return True

	def _identify(self):
		self.connection.privmsg('nickserv', 'identify %s' % self.password)

	def event_logger(self, event):
		pass

	def on_action(self, c, e):
		logger.log_event(self.server, e)

	def on_join(self, c, e):
		logger.log_event(self.server, e)

	def on_part(self, c, e):
		logger.log_event(self.server, e)

	def on_privnotice(self, c, e):
		logger.log_event(self.server, e)

	def on_pubnotice(self, c, e):
		logger.log_event(self.server, e)

	def on_quit(self, c, e):
		logger.log_event(self.server, e)

	def on_nick(self, c, e):
		logger.log_event(self.server, e)

	def on_topic(self, c, e):
		logger.log_event(self.server, e)

	def on_mode(self, c, e):
		logger.log_event(self.server, e)


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

class HeadRequest(Request):
	"""Perform a HEAD request instead of a GET request using urllib2.urlopen"""
	def get_method(self):
		return "HEAD"

def main():
	c = get_config('CONNECTION')
	bot = GentooBot(c['server'],c['port'],c['channel'],c['nick'], c['password'],
		c['reconnect'])
	logger.logger.warning('Connecting %s to %s in %s' % (c['nick'],c['channel'],
		c['server']))
	signal(SIGINT, bot.quit)
	try:
		bot.start()
	except Exception as e:
		logger.error_log(e)
		bot.quit()

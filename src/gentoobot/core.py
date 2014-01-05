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

import re, random, json, time, thread, signal
from urllib2 import urlopen, Request
from urlparse import urlparse
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import irc.bot
from irc.client import NickMask, Event
from bs4 import BeautifulSoup

from gentoobot import logger
from gentoobot.config import get_config, load_db, config_base

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
		self.admins = load_db(server, "admins")

		# This is the bots original nick, used for ghosting.
		self.my_nick = nick
		self.nick = nick
		self.server = server
		self.port = int(port)
		self.password = password

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

	def on_privmsg(self, c, e):
		logger.log_event(self.server, e)
		user = e.source
		msg = e.arguments[0]

	def on_kick(self, c, e):
		logger.log_event(self.server, e)
		time.sleep(self.reconnect)
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

	def on_nicknameinuse(self, c, e):
		self.nick += '_'
		c.nick(self.nick)

		if self.password:
			self._ghost(self.password)

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

	def quit(self, *args):
		self.disconnect('Bye Bye')
		logger.logger.warning("Disconnected from the server!")
		raise SystemExit

	def _identify(self):
		self.connection.privmsg('nickserv', 'identify %s' % self.password)

	def _ghost(self, password):
		self.connection.privmsg('nickserv', 'ghost %s %s' % (self.my_nick, password))
		self.connection.nick(self.my_nick)
		self.nick = self.my_nick[:]
		self._identify()

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
	signal.signal(signal.SIGINT, bot.quit)

	try:
		bot.start()
	except Exception as e:
		logger.error_log(e)
		bot.quit()

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
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import irc.bot

from commands import commands
import config

class GentooBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667, reconnect=5):
		server_spec = irc.bot.ServerSpec(server, port)
		irc.bot.SingleServerIRCBot.__init__(self, [server_spec], nickname, nickname,
				reconnection_interval=reconnect)
		self.channel = channel
		self.reconnect = reconnect
		self.nickname = nickname
		self.server = server
		self.port = port

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
		nick = e.source.nick
		ig_keywords = ('ubuntu', 'redhat', 'fedora', 'mint', 'debian',
				'windows', 'mac', 'arch', 'microsoft', 'apple', 'bsd', 'minix',
				'haiku', 'BeOS', 'TempleOS', 'OSX', 'Plan9', 'Unix', 'SparrowOS',
				'Wangblows', "linux", "lunix", "archlinux")
		for keyword in ig_keywords:
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
		msg = commands.do_command(e.arguments[0])
		if msg:
			self.say(c, msg)

	def say(self, c, message):
		"""Print message in the channel"""
		c.privmsg(self.channel, message)

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

	Gentoo_Bot = GentooBot(args.channel, args.nick, server=args.server, port=args.port)
	try:
		Gentoo_Bot.start()
	except Exception as e:
		# Log errors.
		with open('/tmp/gentoobot_error.log', 'a') as error_log:
			error_log.write(sys.exc_info()[2])
		sys.exit(sys.exc_info()[2])

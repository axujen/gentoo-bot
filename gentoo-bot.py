#!/usr/bin/env python3
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

import irc.bot
ig_server = irc.bot.ServerSpec('irc.installgentoo.com')

class GentooBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667):
		irc.bot.SingleServerIRCBot.__init__(self, [server], nickname, nickname)
		self.channel = channel

	def on_welcome(self, c, e):
		"""docstring for on_welcome"""
		c.join(self.channel)

	def on_pubmsg(self, c, e):
		"""docstring for on_pubmsg"""
		msg = e.arguments[0]
		nick = e.source.split('!', 1)[0]
		if 'windows' in msg:
			c.privmsg(self.channel, "%s: Install Gentoo" % nick)

if __name__ == '__main__':
	Gentoo_Bot = GentooBot("#/g/test", "GentooBot", ig_server)
	Gentoo_Bot.start()

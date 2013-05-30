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

from argparse import ArgumentParser, REMAINDER

from pylast import LastFMNetwork
from gentoobot.config import lastfm

# Lastfm instance
last = LastFMNetwork(api_key = lastfm['api_pub'], api_secret = lastfm['api_secret'])

# User arguments.
commands = ArgumentParser(description="GentooBot is an annoying bot "\
		"designed to spam install gentoo on users, all other features "\
		"are simply there to keep people from ignoring the bot.\n"\
		"Made by axujen <https://github.com/axujen/gentoo-bot>",
		add_help=False, prefix_chars=":")
commands.add_argument(":np", ":nowplaying", metavar="user", dest="np",
		nargs=REMAINDER,
		help="display current or last played song by `user`.")
commands.add_argument(":compare", metavar="user1 user2", dest="compare",
		nargs=REMAINDER,
		help="compare `user1` and `user2` lastfm profiles.")

def lastfm_compare(user1, user2):
	"""Compare 2 lastfm users."""
	try:
		comparer = last.get_user(user1)
		compare = comparer.compare_with_user(user2)
	except WSError as e:
		return(e.reason)
		return
	rating = int(compare[0])*100
	try:
		common_artists = ', '.join([artist.name for artist in compare[1]])
	except IndexError:
		common_artists = 'None!'

	return("Compatibility between %s and %s is %d%%! Common artists are: %s."\
				% (user1, user2, common_artists))

def lastfm_np(user):
	"""Playing current or last playing song by the user."""
	user = last.get_user(user)
	np = user.get_now_playing()
	if not np:
		last_song = user.get_recent_tracks(2)[0]
		return("%s last played: %s" % (user, last_song))
	else:
		return("%s is playing: %s" % (user, np))

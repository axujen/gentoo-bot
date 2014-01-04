GentooBot
=========
Is an annoying bot designed to spam users in a channel with
install gentoo messages. Features have been added to the bot to give
users a reason not to put the bot on their ignore list.

#Features:
* Lastfm now playing and taste compare.
* Link title resolving.
* Install Gentoo.

#Planned Features:
* Lastfm recommends.
* DuckDuckGo im feeling ducky searches.
* Better 4chan title resolving.
* Random fun messages every once in a while.

#Usage:
	gentoobot [-h] [-s server] [-p port] [-n nick] [-c channel]
	
	optional arguments:
	  -h, --help			"show this help message and exit"
	  -s, --server	server	"irc server to connect to."
	  -p, --port	port	"server port."
	  -n, --nick	nick	"bot's name."
	  -c, --channel	channel	"channel to connect to."
	  --config		dif		"alternative config directory."

#Requirements:
* The bot is only being tested under GNU/Linux and FreeBSD 9 with python2.7
* [python-irc](https://pypi.python.org/pypi/irc)
* [pylast](https://pypi.python.org/pypi/pylast)
* [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup)

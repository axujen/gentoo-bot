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

import re, os, random
from shutil import copy2

import redis

from gentoobot.logger import logger

class Brain(object):
	def __init__(self, file):
		self.db = redis.Redis('localhost', db=0)

	def save_brain(self):
		"""Save the brain to a file"""
		logger.warning('Writing the brain database')
		self.db.save()
		logger.warning('Finished writting the brain database')

	def process_line(self, line):
		words = re.sub(r'[^a-zA-Z\s]', '', line).split()
		for id, word in zip(xrange(len(words)-2), words):
			next = words[id+1]
			val1 = words[id+2]

			key = ' '.join((word, next)).lower()
			self.db.sadd(key, val1)
		return words

	def generate_sentence(self, msg):
		"""Generate a sentence based on msg"""
		logger.warning('Generating sentence based on %s', msg)
		words = self.process_line(msg)
		seed = random.randint(0, len(words)-2)
		seed, next, = words[seed], words[seed+1]
		w1, w2 = seed, next
		sentence, w = [w1, w2], 2
		for i in xrange(random.randint(len(words)-5, len(words)+5)):
			key = ' '.join((w1, w2)).lower()
			if self.db.exists(key):
				w3 = self.db.srandmember(key)
			else:
				try:
					w3 = words[w]
				except IndexError:
					return ' '.join(sentence)
			sentence.append(w3)
			w1, w2 = w2, w3
			w += 1
		return ' '.join(sentence)

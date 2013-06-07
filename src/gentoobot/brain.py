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

import re, json, random, os
from shutil import copy2
from collections import defaultdict

from gentoobot.logger import logger

class Brain(object):
	def __init__(self, file):
		self.file = file
		self.brain = self.populate_brain(file)

	def populate_brain(self, file):
		"""Populate the brain from a json file"""
		logger.warning('Populating the bots brain from %s', file)
		brain = defaultdict(set)
		with open(file, 'r') as f:
			tmp_brain = json.load(f)

		for item in tmp_brain:
			brain[item] = set(tmp_brain[item])

		# backup the original brain just in case.
		bkp = '.'.join((file, 'bkp'))
		if os.path.exists(bkp):
			os.remove(bkp)
		logger.warning('backing up the brain file to %s' % bkp)
		copy2(file, bkp)

		logger.warning('Loaded brain, found %d keys', len(brain))
		return brain

	def save_brain(self):
		"""Save the brain to a file"""
		logger.warning('Writing the brain database, this might take a while.')
		brain = {}
		for item in self.brain:
			brain[item] = list(self.brain[item])
		with open(self.file, 'w') as buffer_file:
			json.dump(brain, buffer_file)
		logger.warning('Finished writting the brain database')

	def process_word(self, word):
		word = re.sub(r'[^\w]+', '', word)
		return word

	def process_line(self, line):
		words = line.split()
		linebrain = defaultdict(set)
		for id, word in zip(xrange(len(words)-3), words):
			word = self.process_word(word)
			next = self.process_word(words[id+1])

			val1 = self.process_word(words[id+2])
			val2 = self.process_word(words[id+3])

			key = ' '.join((word, next))
			linebrain[key].update(( val1, val2 ))
			self.brain[key].update(( val1, val2 ))

		return linebrain

	def generate_sentence(self, msg):
		"""Generate a sentence based on msg"""
		logger.warning('Generating sentence based on %s', msg)
		words = msg.split()
		seed = random.randint(0, len(words)-2)
		seed, next, = words[seed], words[seed+1]
		w1, w2 = seed, next
		sentence, w = [w1, w2], 2
		for i in xrange(random.randint(len(words)-5, len(words)+5)):
			key = ' '.join((w1, w2)).lower()
			if key in self.brain:
				w3 = random.choice(list(self.brain[key]))
			else:
				try:
					w3 = words[w]
				except IndexError:
					return ' '.join(sentence)
			sentence.append(w3)
			w1, w2 = w2, w3
			w += 1
		return ' '.join(sentence)

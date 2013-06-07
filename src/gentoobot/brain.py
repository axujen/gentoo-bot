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

import re, json, random
import os.path
from shutil import copy2
from collections import defaultdict
from thread import start_new_thread
from signal import signal, SIGINT, SIG_IGN, SIG_DFL

from gentoobot.logger import logger
from gentoobot.config import config_base

class Brain(object):
	def __init__(self, file):
		self.file = file
		self.brain = self.populate_brain(file)
		self.buffer, self.max_buffer = 0, 10

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
		self.buffer += 1
		if self.buffer >= self.max_buffer:
			logger.warning('Writing the buffer file!')
			brain = {}
			for item in self.brain:
				brain[item] = list(self.brain[item])
			with open(self.file, 'w') as buffer_file:
				json.dump(brain, buffer_file)
			self.buffer = 0
			logger.warning('Finished writting the buffer file!')

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
		signal(SIGINT, SIG_IGN)
		self.save_brain()
		signal(SIGINT, SIG_DFL)

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

brain_file =  os.path.join(config_base, 'brain.txt')
brain = Brain(brain_file)

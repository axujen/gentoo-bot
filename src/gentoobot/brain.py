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
		self.buffer, self.max_buffer = 8, 10

	def populate_brain(self, file):
		"""Populate the brain from a json file"""
		logger.warning('Populating the bots brain from %s', file)
		with open(file, 'r') as f:
			tmp_brain = json.load(f)
		brain = defaultdict(list)

		for item in tmp_brain:
			brain[item] = tmp_brain[item]

		# backup the original brain just in case.
		bkp = '.'.join((file, 'bkp'))
		if os.path.exists(bkp):
			os.remove(bkp)
		logger.warning('backing up the brain file to %s' % bkp)
		copy2(file, bkp)

		logger.warning('Loaded brain, found %d keys', len(brain))
		return brain

	def save_brain(self,):
		"""Save the brain to a file"""
		self.buffer += 1
		if self.buffer >= self.max_buffer:
			logger.warning('Writing the buffer file!')
			with open(self.file, 'w') as buffer_file:
				json.dump(self.brain, buffer_file)
			logger.warning('Finished writting the buffer file!')

	def process_word(self, word):
		word = re.sub(r'[^\w]+', '', word)
		return word

	def process_line(self, line):
		words = line.split()
		for id, word in zip(range(len(words)-3), words):
			word = self.process_word(word)
			next = self.process_word(words[id+1])

			val1 = self.process_word(words[id+2])
			val2 = self.process_word(words[id+3])

			key = ' '.join((word, next))
			self.brain[key] += [val1, val2]

		signal(SIGINT, SIG_IGN)
		self.save_brain()
		signal(SIGINT, SIG_DFL)

	def generate_sentence(self, msg):
		"""Generate a sentence based on msg"""
		logger.warning('Generating sentence based on %s', msg)
		sentence = msg.split()
		gen_sentence = []
		length = len(sentence)
		if length > 2:
			seed = random.randint(0, length-1)
			w1, w2 = sentence[seed], sentence[seed+1]
		else:
			w1, w2 = random.choice(self.brain.keys()).split()
		for i in xrange(random.randint(10, 20)):
			gen_sentence.append(w1)
			key = ' '.join((w1, w2))
			if key in self.brain.keys():
				w1, w2 = w2, random.choice(self.brain[key])
			else:
				w1, w2 = w2, random.choice(self.brain[random.choice(self.brain.keys())])
		gen_sentence.append(w2)
		return ' '.join(gen_sentence)

brain_file =  os.path.join(config_base, 'brain.txt')
brain = Brain(brain_file)

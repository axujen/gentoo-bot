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
from collections import defaultdict

from gentoobot.logger import logger
from gentoobot.config import config_base

def populate_brain(file):
	"""Populate the brain from a json file"""
	logger.warning('Populating the bots brain from %s', file)
	with open(file, 'r') as f:
		data = json.load(f)
		for item in data:
			brain[item] = data[item]

brain = defaultdict(list)
brain_file =  os.path.join(config_base, 'brain.txt')
populate_brain(brain_file)

def process_word(word):
	word = re.sub(r'[^\w]+', '', word)
	return word

def process_line(line):
	words = line.split()
	for id, word in enumerate(words):
		try:
			next = process_word(words[id+1])
			val = process_word(words[id+2])
		except IndexError:
			with open(brain_file, 'w') as brn:
				json.dump(brain, brn)
			return
		word = process_word(word)

		if None in (word, next, val):
			return

		key = ' '.join((word, next)).lower()
		brain[key].append(val)

		try:
			val2 = process_word(words[id+3])
		except IndexError:
			with open(brain_file, 'w') as brn:
				json.dump(brain, brn)
			return
		if val2 != None:
			brain[key].append(val2)
		with open(brain_file, 'w') as brn:
			json.dump(brain, brn)

def generate_sentence(msg):
	"""Generate a sentence based on msg"""
	logger.warning('Generating sentence based on %s', msg)
	sentence = msg.split()
	for id, word in enumerate(sentence):
		try:
			next = sentence[id+1]
		except IndexError:
			return ' '.join(sentence)
		key = ' '.join((word, next)).lower()
		if key in brain.keys():
			sentence[id] = random.choice(brain[key])

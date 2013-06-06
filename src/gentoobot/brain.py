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
			# remove duplicates
			brain[item] = set(data[item])

brain = defaultdict(set)
brain_file =  os.path.join(config_base, 'brain.txt')
populate_brain(brain_file)
global buffer
buffer = 0

def add_to_brain(key, value):
	"""docstring for add_to_brain"""
	global buffer
	brain[key].add(value)
	if buffer >= 2:
		buffer = 0
		saved_brain = defaultdict(list)
		for item in brain:
			saved_brain[item] = list(brain[item])
		with open(brain_file, 'w') as brn:
			json.dump(saved_brain, brn)

def process_word(word):
	word = re.sub(r'[^\w]+', '', word)
	return word

def process_line(line):
	global buffer
	words = line.split()
	buffer += 1
	for id, word in enumerate(words):
		try:
			next = process_word(words[id+1])
			val = process_word(words[id+2])
		except IndexError:
			return
		word = process_word(word)

		if None in (word, next, val):
			return

		key = ' '.join((word, next)).lower()
		add_to_brain(key, val)

		try:
			val2 = process_word(words[id+3])
		except IndexError:
			return
		if val2 != None:
			add_to_brain(key, val2)

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

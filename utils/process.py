#!/usr/bin/env python2.7
import re, redis

# A list of file in the current directory to parse
files = ['sentences.txt']
# db number
db_num = 0
# IF true, the database will cleared before being repopulated with the new files.
clear = False

db = redis.Redis(db=0)
if clear:
	db.flushdb()

def process_words(words):
	if len(words) < 3:
		return

	for id, word in zip(range(len(words)-2), words):
		next = words[id+1]
		val = words[id+2]

		key = ' '.join((word, next)).lower()
		db.sadd(key, val)

def process_file(file):
	with open(file, 'r') as f:
		for line in f.readlines():
			words = re.sub(r'[^a-zA-Z\s]', '', line).split()
			process_words(words)
	return

for file in files:
	print('Processing file %s' % file)
	process_file(file)
	print('Done processing %s' % file)

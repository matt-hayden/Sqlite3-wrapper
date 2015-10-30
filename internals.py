#!/usr/bin/env python3
import collections
import math

import descriptives


if __debug__:
	import sqlite3 as sqlite
	sqlite.enable_callback_tracebacks(True)


class SqliteAggregate:
	"""
	Abstract for classes that implement the Sqlite aggregate function API:
		__init__(self)
		step(self, value)
		finalize(self)
	"""
	pass
class DistributionAggregate(SqliteAggregate, descriptives.Descriptives):
	"""
	Abstract for classes with a .freq member, and this member works identically to collections.Counter.
	"""
	def step(self, value):
		self.freq[value] += 1
class Sqlite_mode(DistributionAggregate):
	def finalize(self):
		mode, _ = self.mode
		return mode
class Sqlite_mode_freq(DistributionAggregate):
	"""
	This is an example and not used in production.
	"""
	sep = ';'
	def finalize(self):
		m, f = self.mode_freq
		return '{m}{sep}{f}'.format(**locals())
import json
class Sqlite_descriptives(DistributionAggregate):
	def finalize(self):
		return json.dumps(self.get_descriptives())


class ListAggregate(SqliteAggregate):
	"""
	Abstract for classes returning a semicolon-separated list of values, stored in self.values
	"""
	sep = ';'
	def __init__(self, values=[]):	## example ##
		self.values = values		##
	def finalize(self):
		n = len(self.values)
		if n == 0:
			return None
		if n == 1:
			return self.values.pop()
		else:
			return self.sep.join(str(i) for i in self.values)
class Sqlite_first_n(ListAggregate):
	def __init__(self):
		self.values = []
		self.init = False
	def step(self, value, arg=1):
		if not self.init:
			assert 0 < arg
			self.free, self.init = arg, True
		if self.free:
			self.values.append(value)
			self.free -= 1
class Sqlite_last_n(ListAggregate):
	def __init__(self):
		self.init = False
	def step(self, value, arg=1):
		if not self.init:
			self.values, self.init = collections.deque([], arg), True
		self.values.append(value)


def register_aggregates(con):
	con.create_aggregate("DESCRIPTIVES",	1, Sqlite_descriptives)
	con.create_aggregate("FIRST",			1, Sqlite_first_n)
	con.create_aggregate("LAST",			1, Sqlite_last_n)
	con.create_aggregate("FIRSTN",			2, Sqlite_first_n)
	con.create_aggregate("LASTN",			2, Sqlite_last_n)


if __name__ == '__main__':
	from wrapper import SqliteWrapper
	cq = 'create table some_table(i1, f1);'
	iq = 'insert into some_table(i1, f1) values (?,?);'
	with SqliteWrapper() as db:
		register_aggregates(db.con)
		with db.ccursor() as cur:
			cur.execute(cq)
			cur.executemany(iq, zip(range(0, 10000), range(5000, -5000, -1)) )
			[fields] = cur.execute('select descriptives(i1), descriptives(f1) from some_table;').fetchall()
	import pprint
	pprint.pprint(fields)

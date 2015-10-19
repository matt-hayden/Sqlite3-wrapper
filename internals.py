#!/usr/bin/env python3
import collections
import math

import descriptives


if __debug__:
	import sqlite3 as sqlite
	sqlite.enable_callback_tracebacks(True)


class SqliteAggregate:
	"""Classes that implement the Sqlite aggregate function API:
		__init__(self)
		step(self, value)
		finalize(self)
	"""
	pass
class DistributionAggregate(SqliteAggregate, descriptives.Descriptives):
	"""Classes with a .freq member, a-la collections.Counter
	"""
	def step(self, value):
		self.freq[value] += 1
class Sqlite_mode(DistributionAggregate):
	def finalize(self):
		mode, _ = self.mode
		return mode
class Sqlite_mode_freq(DistributionAggregate):
	sep = ';'
	def finalize(self):
		m, f = self.mode_freq
		return '{m}{sep}{f}'.format(**locals())
class Sqlite_descriptives(DistributionAggregate):
	def finalize(self):
		return self.to_json()


class ListAggregate(SqliteAggregate):
	"""Classes returning a semicolon-separated list of values
	"""
	sep = ';'
	def finalize(self):
		n = len(self.values)
		if n == 0:
			return None
		if n == 1:
			return self.values.pop()
		else:
			return self.sep.join(str(i) for i in self.values)
class Sqlite_first_n(ListAggregate):
	def __init__(self, limit=1):
		assert 0 < limit
		self.values = []
		self.limit, self.notfull = limit, (0 < limit)
	def step(self, value):
		if self.notfull:
			self.values.append(value)
			self.notfull = (len(self.values) < self.limit)
class Sqlite_last_n(ListAggregate):
	def __init__(self, limit=1):
		assert 0 < limit
		self.values = collections.deque([], limit)
	def step(self, value):
		self.values.append(value)


def register_aggregates(con):
	con.create_aggregate("DESCRIPTIVES",	1, Sqlite_descriptives)
	con.create_aggregate("FIRST",			1, Sqlite_first_n)
	con.create_aggregate("LAST",			1, Sqlite_last_n)
	con.create_aggregate("MODE",			1, Sqlite_mode)


if __name__ == '__main__':
	from wrapper import SqliteWrapper
	cq = 'create table some_table(i1, f1);'
	iq = 'insert into some_table(i1, f1) values (?,?);'
	with SqliteWrapper() as db:
		register(db.con)
		with db.ccursor() as cur:
			cur.execute(cq)
			cur.executemany(iq, zip(range(0, 100), range(50, -50, -1)) )
			print(cur.execute('select descriptives(i1), descriptives(f1) from some_table;').fetchall())

#!/bin/bash
import collections
import sqlite3 as sqlite

if __debug__:
	sqlite.enable_callback_tracebacks(True)

#
class SqliteAggregate:
	pass

class DistributionAggregate(SqliteAggregate):
	def __init__(self):
		self.freq = collections.Counter()
	def step(self, value):
		self.freq[value] += 1
class MODE(DistributionAggregate):
	def finalize(self):
		mode, _ = self.freq.most_common(1)
		return mode
class MODEFREQ(DistributionAggregate):
	sep = ';'
	def finalize(self):
		return '{1[0]}{0}{1[1]}'.format(self.sep, self.freq.most_common(1))


class ListAggregate(SqliteAggregate):
	sep = ';'
	def finalize(self):
		n = len(self.values)
		if n == 0:
			return None
		if n == 1:
			return self.values.pop()
		else:
			return self.sep.join(str(i) for i in self.values)
class FIRST(ListAggregate):
	def __init__(self, limit=1):
		assert 0 < limit
		self.values = []
		self.limit, self.notfull = limit, (0 < limit)
	def step(self, value):
		if self.notfull:
			self.values.append(value)
			self.notfull = (len(self.values) < self.limit)
class LAST(ListAggregate):
	def __init__(self, limit=1):
		assert 0 < limit
		self.values = collections.deque([], limit)
	def step(self, value):
		self.values.append(value)
#
def connect(*args, **kwargs):
	con = sqlite.connect(*args, **kwargs)
	con.create_aggregate("MODE",	1, MODE)
	con.create_aggregate("FIRST",	1, FIRST)
	con.create_aggregate("LAST",	1, LAST)
	return con
#
if __name__ == '__main__':
	from contextlib import closing
	from pprint import pprint
	con = connect(':memory:')
	with closing(con.cursor()) as cur:
		cur.execute('create table test(i1, i2)')
		cur.execute('insert into test(i1, i2) values (1, 1)')
		cur.execute('insert into test(i1, i2) values (2, 0)')
		cur.execute('insert into test(i1, i2) values (3, 1)')
		cur.execute('insert into test(i1, i2) values (4, 0)')
		cur.execute('select i2, FIRST(i1), LAST(i1) from test GROUP BY i2')
		pprint(cur.fetchall())
		cur.execute('select FIRSTN(i1,2), LASTN(i1,8) from test')
		pprint(cur.fetchall())

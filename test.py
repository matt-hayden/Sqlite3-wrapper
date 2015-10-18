#!/usr/bin/env python3
"""Exercise sqlite3 wrapper functions, emitting numpy objects
"""
from wrapper import SqliteWrapper
from sqlite_numpy import *

cq = '''CREATE TABLE some_table
(id		INTEGER		PRIMARY KEY,
 added		DATETIME	DEFAULT CURRENT_TIMESTAMP,
 some_text	TEXT(1023)	NOT NULL,
 some_int	INTEGER,
 some_real	REAL,
 some_numeric	NUMERIC
 );'''
iq = 'insert into some_table ( some_text, some_int, some_real, some_numeric) values (?,?,?,?);'

with SqliteWrapper(commit_on_exit=True) as sw:
	with sw.ccursor() as cur:
		cur.execute(cq)
		for x in range(0, -250, -10):
			cur.execute(iq, [10**x]*4)
		for n in range(16,62):
			cur.execute(iq, [1<<n]*4)
		ntable = np.fromiter(cur.execute('select * from some_table;'), get_dtype(sw.get_table_info('some_table')) )

statements = [ '''ntable['some_int'].sum()''', '''ntable['added'].min()''' ]
for s in statements:
	print(s)
	print(eval(s))
	print()

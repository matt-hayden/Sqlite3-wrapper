
import numpy as np

import wrapper


def get_title(name, sep=' '):
	tl = []
	for w in name.split('_'):
		uw = w.upper()
		if uw.endswith('ID'):
			tl.append(uw)
		else:
			tl.append(w.title())
	return sep.join(tl) if tl else 'FIELD'
def get_dtype(table_desc):
	# table_desc is the output of get_table_info()
	table_desc.sort(key=lambda row: row.order)
	names = [ r.name for r in table_desc ]
	formats = [ lookup_numpy_format(r.type) for r in table_desc ]
	titles = [ get_title(n) for n in names ]
	return np.format_parser(names=names, formats=formats, titles=titles)
def lookup_numpy_format(sqlite_format, sqlite_width=None):
	print(sqlite_format)
	if ')' in sqlite_format:
		i = sqlite_format.index('(')
		f = sqlite_format[:i]
		w = eval(sqlite_format[i:]) # (n) -> n
		return lookup_numpy_format(f, w)
	if sqlite_format == 'INTEGER':
		return 'i8'
	elif sqlite_format in ('NUMERIC', 'REAL'):
		return 'f8'
	elif sqlite_format == 'TEXT':
		return 'U{:d}'.format(sqlite_width)
		#return 'S{:d}'.format(sqlite_width)
	elif sqlite_format == 'DATETIME':
		return 'datetime64[ms]'
	else:
		raise ValueError("{}({}) not found".format(sqlite_format, sqlite_width))
#
if __name__ == '__main__':
	from pprint import pprint
	import sys

	from wrapper import SqliteWrapper

	sw = SqliteWrapper('test.sqlite')
	iq = 'insert into some_table ( some_text, some_int, some_real, some_numeric) values (?,?,?,?);'
	with sw.ccursor() as cur:
		for x in range(-20, 0):
			cur.execute(iq, [10**x]*4)
		for n in range(16,62):
			cur.execute(iq, [1<<n]*4)
		#table = cur.execute('select * from some_table;').fetchall()
		#my_dtype = get_dtype(sw.get_table_info('some_table'))
		ntable = np.fromiter(cur.execute('select * from some_table;'), get_dtype(sw.get_table_info('some_table')) )
	print("sw.con.commit() to save changes")



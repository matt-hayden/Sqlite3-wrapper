#!/usr/bin/env python3
"""Simple wrapper between Sqlite and numpy data types
"""
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


def lookup_numpy_format(sqlite_format, sqlite_width=None):
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


def get_dtype(table_desc, get_title=get_title):
	"""Example:
		with SqliteWrapper() as db:
			desc = db.get_table_info(your_table)				# persists after cursor and database close()
			dtype = get_dtype(desc)								# ''
			with db.ccursor() as cur:
				rows = cur.execute('select * from your_table')	# iterable
				faster_table = np.from_iter(rows, dtype)		# rows dies with the cursor
	"""
	table_desc.sort(key=lambda row: row.order)
	names = [ r.name for r in table_desc ]
	formats = [ lookup_numpy_format(r.type) for r in table_desc ]
	if get_title:
		titles = [ get_title(n) for n in names ]
	else:
		titles = names
	return np.format_parser(names=names, formats=formats, titles=titles)

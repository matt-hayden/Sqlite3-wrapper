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
def get_dtype(table_desc):
	# table_desc is the output of get_table_info()
	table_desc.sort(key=lambda row: row.order)
	names = [ r.name for r in table_desc ]
	formats = [ lookup_numpy_format(r.type) for r in table_desc ]
	titles = [ get_title(n) for n in names ]
	return np.format_parser(names=names, formats=formats, titles=titles)
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
#

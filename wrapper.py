#!/usr/bin/env python3
import collections
import contextlib
import sqlite3 as sqlite

from internals import register_aggregates


class SqliteWrapper(contextlib.ContextDecorator):
	"""
	Yet another DBAPI wrapper.
	
	If you're comfortable on the connection level, SqliteWrapper.con is a Sqlite3 Connection. con.cursor() will give you a persistant cursor object.

	This wrapper class simply adds some convenience features to Sqlite.
	"""
	def __init__(self, arg=':memory:', commit_on_exit=None, **kwargs):
		if isinstance(arg, sqlite.Connection):
			self.con = arg
		elif isinstance(arg, str):
			self.con = sqlite.connect(arg, **kwargs)
		else:
			raise ValueError(arg)
		register_aggregates(self.con)
		self.commit_on_exit = commit_on_exit or False
	def __enter__(self):
		assert self.con
		return self
	def __exit__(self, *exc):
		assert self.con
		if self.commit_on_exit:
			self.con.commit()
		self.con.close()
		return False
	def ccursor(self):
		"""
		Context-aware cursor object, which cannot be used like the usual DBAPI cursor.

		An example:
			with db.ccursor() as cur:
				# cur is a DBAPI cursor, which is closed after this with-block
				cur.execute(...)
				cur.fetch(...)

		This will not work:
			cur = db.ccursor()
			cur.execute(...) # cur is a 'closing' object, which is useless without a with-block
		"""
		return contextlib.closing(self.con.cursor())
	"""
	Field and row operations:
	"""
	class SqliteFieldDescription(collections.namedtuple('SqliteFieldDescription', 'order name type nullable default primary_key_index')):
		pass
	def get_table_info(self, tablename, rf=SqliteFieldDescription):
		assert ';' not in tablename
		with self.ccursor() as cur:
			fields_rows = cur.execute('PRAGMA table_info('+tablename+');').fetchall()
		return [ rf(*row) for row in fields_rows ]
	def get_row_factory(self, tablename):
		"""
		Returns desc, factory
			desc is a list of field descriptors
			factory can be called on a tuple to form a Row object, which has field names as members
		"""
		desc = self.get_table_info(tablename)
		class Row(collections.namedtuple('Row', [ f.name for f in desc ])):
			"""
			This class represents a database row coming out of a query. It is simple and not intended to be manipulated and re-used in execute statements.
			"""
			pass
		return desc, Row
	"""
	Introspection operations:
	"""
	class SqliteDatabaseDescription(collections.namedtuple('SqliteDatabaseDescription', 'order main name')):
		pass
	@property
	def database_list(self, rf=SqliteDatabaseDescription):
		with self.ccursor() as cur:
			databases_rows = cur.execute('PRAGMA database_list;').fetchall()
		return [ rf(*row) for row in databases_rows ]
	@property
	def sqlite_master(self):
		"""
		Returns a tree, not a list of rows
		"""
		tree = collections.defaultdict(list)
		_, rf = self.get_row_factory('sqlite_master')
		with self.ccursor() as cur:
			master_rows = cur.execute('select * from sqlite_master;').fetchall()
		rows = [ rf(*row) for row in master_rows ]
		for row in rows:
			tree[row.type].append(row)
		return tree
	@property
	def tables(self):
		return { o.name: o for o in self.sqlite_master['table'] if o.type == 'table' }
#
#

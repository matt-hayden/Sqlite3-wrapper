#!/usr/bin/env python3
import subprocess
import sys

from wrapper import SqliteWrapper

args = sys.argv[1:]

if sys.stdin.isatty():
	print("Expecting user input")
else:
	print("Redirecting stdin")
	proc = subprocess.Popen(['scripts/shell_wrapper.bash'], stdout=subprocess.PIPE)
	out, _ = proc.communicate()
	table_name, db_filename = out.decode('UTF-8').split()
	print(db_filename)

with SqliteWrapper(db_filename or args[0]) as db:
	for tn, tp in db.tables.items():
		print(tn)
		print(tp.type)
		print()
	print(db.sqlite_master)

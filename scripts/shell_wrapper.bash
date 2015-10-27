#!/bin/bash
# This script simply wraps an input stream for use with sqlite.
# example: new_db=$(some_command | this_script)
# example: new_db=$(this_script some_command_with_args)
# output is a filename in a temporary directory, with some attempt to keep the content's permissions private

# TODO: I suspect mktemp is slightly different on Linux

set -e
exec 6<&0 # save stdin

umask 077
export TMPDIR=$(mktemp -t "$$" -d) || exit -1

: ${DB=$(mktemp -t sqlite)} ${PIPE=$(mktemp -t pipe)}
: ${SQLITE=sqlite3} ${mode=tab} ${operation=import} ${table_name=$(date +'import_%Y%m%d_%H%M')}


[[ -e "$PIPE" ]] || mkfifo "$PIPE" || exit -1


if [[ $@ ]]
then
	eval "$@" <&6 >"$PIPE" &
else
	cat - <&6 >"$PIPE" &
fi
exec 0<&6 6<&- # restore stdin

case $operation in
	fts*)
		$SQLITE "$DB" <<- EOL
			.tables
			CREATE VIRTUAL TABLE "$table_name" USING fts4(tokenize=porter);
			.mode line
			.import "$PIPE" "$table_name"
			.tables
		EOL
		;;
	import*)
		$SQLITE "$DB" <<- EOL
			.tables
			.mode $mode
			.import "$PIPE" "$table_name"
			.tables
		EOL
		;;
	restore*)
		$SQLITE "$DB" <<- EOL
			.tables
			.restore "$table_name" "$PIPE"
			.tables
		EOL
		;;
	*) usage ;;
esac

[[ -p "$PIPE" ]] && rm "$PIPE"
echo "$DB"

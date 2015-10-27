#!/bin/bash
set -e
exec 6<&0 # save stdin

: ${SQLITE=sqlite3}
export TMPDIR=$(mktemp -t "$$" -d) || exit -1

mode=tab
operation=fts
table_name=$(date +'import_%Y%m%d_%H%M')


if ! [[ $DB ]]
then
	DB="$TMPDIR/$$.sqlite"
fi
if ! [[ $PIPE ]]
then
	PIPE="$TMPDIR/$$.pipe"
	[[ -e "$PIPE" ]] || mkfifo "$PIPE" || exit -1
fi


if [[ $@ ]]
then
	cmd="$@"
elif [[ -t 2 ]]
then
	cmd="pv -l"
else
	cmd="cat -"
fi


eval $cmd <&6 >"$PIPE" &

case $operation in
	fts*)
		$SQLITE $DB <<- EOL
			.tables
			CREATE VIRTUAL TABLE "$table_name" USING fts4(tokenize=porter);
			.mode line
			.import "$PIPE" "$table_name"
			.tables
		EOL
		;;
	import*)
		$SQLITE $DB <<- EOL
			.tables
			.mode $mode
			.import "$PIPE" "$table_name"
			.tables
		EOL
		;;
	restore*)
		$SQLITE $DB <<- EOL
			.tables
			.restore "$table_name" "$PIPE"
			.tables
		EOL
		;;
	*) usage ;;
esac

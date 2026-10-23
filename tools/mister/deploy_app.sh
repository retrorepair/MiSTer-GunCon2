#!/bin/sh
# Runs ON the MiSTer. Installs the app and, when uploaded, the physical-disc app, then restarts whichever of the two was running, into the
# same core (its arguments only NAME the core already in the FPGA; starting it with another game's paths does not load that game and wedged
# the app on 2026-10-23), and can then load a game with load_core.
#   /tmp/MiSTer.app   -> /media/fat/MiSTer               (the old one becomes MiSTer.prev; /tmp/MiSTer.clean is kept as MiSTer.clean)
#   /tmp/PhysCD.app   -> /media/fat/MiSTer_Physical-CD   (the card's own copy is kept once as MiSTer_Physical-CD.orig, the last one as .prev;
#                                                         /tmp/PhysCD.clean is kept as MiSTer_Physical-CD.clean)
# MiSTer.ini's main=MiSTer_Physical-CD (in the [PSX], [Saturn], [MegaCD], [TurboGrafx16] sections) makes the app hand over to the second one.
# Sent over ssh with the key, from the repo on the PC, e.g.:
#   tar cf - -C build MiSTer.app MiSTer.clean PhysCD.app PhysCD.clean -C ../tools/mister deploy_app.sh |
#     ssh root@192.168.1.204 "cd /tmp && tar xf - && tr -d '\r' < deploy_app.sh > d.sh && sh d.sh <md5 app> <md5 clean> <md5 physcd> <md5 physcd clean> [game]"
# Pass - - for the physical-disc pair to leave that app alone. The optional last argument is an .mra or .rbf to load with load_core.
want_app="$1"; want_clean="$2"; want_pd="$3"; want_pdc="$4"; new_game="$5"
check() {
	got=$(md5sum "/tmp/$1" | cut -d' ' -f1)
	if [ "$got" != "$2" ]; then echo "the upload of $1 is damaged: md5 $got, wanted $2"; exit 1; fi
}
check MiSTer.app "$want_app"
check MiSTer.clean "$want_clean"
pd=0
if [ -n "$want_pd" ] && [ "$want_pd" != "-" ]; then check PhysCD.app "$want_pd"; check PhysCD.clean "$want_pdc"; pd=1; fi

# the running app (either one) and what it was started with
P=$(pidof MiSTer MiSTer_Physical-CD | tr ' ' '\n' | head -1)
EXE=/media/fat/MiSTer
ARGS=""
if [ -n "$P" ]; then
	EXE=$(tr '\0' '\n' < /proc/$P/cmdline | head -1)
	ARGS=$(tr '\0' '\n' < /proc/$P/cmdline | tail -n +2)
fi
echo "running: pid $P, $EXE, arguments:"; echo "$ARGS"

cd /media/fat
cp -p MiSTer MiSTer.prev
cp /tmp/MiSTer.app MiSTer.new && sync && mv -f MiSTer.new MiSTer
cp /tmp/MiSTer.clean MiSTer.clean
if [ $pd = 1 ]; then
	[ -e MiSTer_Physical-CD.orig ] || cp -p MiSTer_Physical-CD MiSTer_Physical-CD.orig
	cp -p MiSTer_Physical-CD MiSTer_Physical-CD.prev
	cp /tmp/PhysCD.app MiSTer_Physical-CD.new && sync && mv -f MiSTer_Physical-CD.new MiSTer_Physical-CD
	cp /tmp/PhysCD.clean MiSTer_Physical-CD.clean
fi
sync
md5sum MiSTer MiSTer.clean MiSTer.prev MiSTer.stock MiSTer_Physical-CD MiSTer_Physical-CD.clean MiSTer_Physical-CD.orig 2>/dev/null

[ -n "$P" ] && kill $P
sleep 3
# the arguments are file paths with spaces (an MRA name): pass them one per line
echo "$ARGS" > /tmp/mister_args.txt
A1=$(sed -n 1p /tmp/mister_args.txt); A2=$(sed -n 2p /tmp/mister_args.txt)
if [ -n "$A2" ]; then setsid "$EXE" "$A1" "$A2" > /tmp/mister.log 2>&1 < /dev/null &
elif [ -n "$A1" ]; then setsid "$EXE" "$A1" > /tmp/mister.log 2>&1 < /dev/null &
else setsid "$EXE" > /tmp/mister.log 2>&1 < /dev/null &
fi
sleep 12
case "$new_game" in
	*.mra|*.rbf) timeout 8 sh -c "echo \"load_core $new_game\" > /dev/MiSTer_cmd" && echo "load_core sent: $new_game"
	             for i in $(seq 1 40); do sleep 3; pidof MiSTer MiSTer_Physical-CD > /dev/null && [ /tmp/CORENAME -nt /tmp/mister_args.txt ] && break; done ;;
	"") ;;
	*) echo "not loading $new_game: load_core takes an .mra or .rbf only" ;;
esac
echo "core now: $(cat /tmp/CORENAME)"
ps | grep -E '[/]media/fat/MiSTer( |_Physical-CD)' | head -2

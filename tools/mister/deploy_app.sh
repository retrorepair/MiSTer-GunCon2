#!/bin/sh
# Runs ON the MiSTer. Installs the app only (not GunCal) and restarts it into the SAME core and game that were running.
# Sent over ssh with the key (no password), from the repo on the PC:
#   tar cf - -C build MiSTer.app MiSTer.clean -C ../tools/mister deploy_app.sh | ssh root@192.168.1.204 "cd /tmp && tar xf - && tr -d '\r' < deploy_app.sh > d.sh && sh d.sh <md5 app> <md5 clean>"
# /tmp/MiSTer.app is installed as /media/fat/MiSTer (the trace build), /tmp/MiSTer.clean is kept next to it; the old app becomes MiSTer.prev.
# Optional 3rd argument: an .mra (or .rbf) to load after the restart, with load_core, instead of staying in the game that was running.
# The app's own arguments only NAME the core that is already in the FPGA; starting it with another game's paths does not load that game
# (it wedged the app on 2026-10-23: HotD's paths with Viper in the FPGA).
want_app="$1"; want_clean="$2"; new_game="$3"
for f in "MiSTer.app $want_app" "MiSTer.clean $want_clean"; do
	set -- $f
	got=$(md5sum /tmp/$1 | cut -d' ' -f1)
	if [ "$got" != "$2" ]; then echo "the upload of $1 is damaged: md5 $got, wanted $2"; exit 1; fi
done

# what the running app was started with (the launcher starts it as: MiSTer <core rbf> <mra>), so it comes back in the same game
P=$(pidof MiSTer | cut -d' ' -f1)
ARGS=""
[ -n "$P" ] && ARGS=$(tr '\0' '\n' < /proc/$P/cmdline | tail -n +2)
echo "running app pid $P, arguments:"; echo "$ARGS"

cd /media/fat
cp -p MiSTer MiSTer.prev
cp /tmp/MiSTer.app MiSTer.new && sync && mv -f MiSTer.new MiSTer
cp /tmp/MiSTer.clean MiSTer.clean
sync
md5sum MiSTer MiSTer.clean MiSTer.prev MiSTer.stock

[ -n "$P" ] && kill $P
sleep 3
# the arguments are file paths with spaces (an MRA name): pass them one per line
echo "$ARGS" > /tmp/mister_args.txt
A1=$(sed -n 1p /tmp/mister_args.txt); A2=$(sed -n 2p /tmp/mister_args.txt)
if [ -n "$A2" ]; then setsid /media/fat/MiSTer "$A1" "$A2" > /tmp/mister.log 2>&1 < /dev/null &
elif [ -n "$A1" ]; then setsid /media/fat/MiSTer "$A1" > /tmp/mister.log 2>&1 < /dev/null &
else setsid /media/fat/MiSTer > /tmp/mister.log 2>&1 < /dev/null &
fi
sleep 12
case "$new_game" in
	*.mra|*.rbf) timeout 8 sh -c "echo \"load_core $new_game\" > /dev/MiSTer_cmd" && echo "load_core sent: $new_game"
	             for i in $(seq 1 40); do sleep 3; pidof MiSTer > /dev/null && grep -q . /tmp/CORENAME && [ /tmp/CORENAME -nt /tmp/mister_args.txt ] && break; done ;;
	"") ;;
	*) echo "not loading $new_game: load_core takes an .mra or .rbf only" ;;
esac
echo "core now: $(cat /tmp/CORENAME)"
ps | grep '[/]media/fat/MiSTer' | head -2

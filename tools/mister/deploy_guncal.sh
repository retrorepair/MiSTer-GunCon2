#!/bin/sh
# Runs ON the MiSTer; sent by tools/mister/deploy_guncal.bat (over ssh: one password prompt, then it all runs).
# It finds in /tmp: GunCal.rbf (the calibration core), MiSTer.app (the app to install) and MiSTer.clean (the app without the trace, kept next to it).
# Arguments: the md5 of each of the three, in that order. What it does: prints the video info the app logged for the running core, backs up the
# app and the core that are installed (MiSTer.prev, GunCal.rbf.prev), installs the new ones, restarts the app and loads GunCal.
want_rbf="$1"; want_app="$2"; want_clean="$3"
for f in "GunCal.rbf $want_rbf" "MiSTer.app $want_app" "MiSTer.clean $want_clean"; do
	set -- $f
	got=$(md5sum /tmp/$1 | cut -d' ' -f1)
	if [ "$got" != "$2" ]; then echo "the upload of $1 is damaged: md5 $got, wanted $2"; exit 1; fi
done
echo "--- what the app logged about the running core's video (guncal_apply.log, last lines) ---"
tail -12 /tmp/guncal_apply.log 2>/dev/null
echo "--- installing ---"
cd /media/fat
cp -p MiSTer MiSTer.prev
cp /tmp/MiSTer.app MiSTer.new && sync && mv -f MiSTer.new MiSTer
cp /tmp/MiSTer.clean MiSTer.clean
cd /media/fat/_Utility
[ -e GunCal.rbf ] && cp -p GunCal.rbf GunCal.rbf.prev
cp /tmp/GunCal.rbf GunCal.rbf.new && sync && mv -f GunCal.rbf.new GunCal.rbf
sync
md5sum /media/fat/MiSTer /media/fat/MiSTer.clean /media/fat/MiSTer.prev /media/fat/MiSTer.stock /media/fat/_Utility/GunCal.rbf
echo "--- restarting the app and loading GunCal ---"
P=$(ps | grep '[/]media/fat/MiSTer' | awk '{print $1}' | head -1)
[ -n "$P" ] && kill $P
sleep 3
cd /media/fat
setsid /media/fat/MiSTer > /tmp/mister.log 2>&1 < /dev/null &
sleep 12
timeout 8 sh -c 'echo "load_core /media/fat/_Utility/GunCal.rbf" > /dev/MiSTer_cmd'
sleep 10
echo "core now: $(cat /tmp/CORENAME)"
ps | grep '[/]media/fat/MiSTer' | head -2

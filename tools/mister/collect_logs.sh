#!/bin/sh
# Runs ON the MiSTer (sent over ssh by fetch_logs.bat): gathers what is needed to see why the gun misbehaves and writes ONE gzip'd tar to stdout.
# It only reads; the only thing it creates is /tmp/lc_collect, which it removes again.
D=/tmp/lc_collect
rm -rf $D; mkdir -p $D
{
	date; uname -a; uptime
	echo "core: $(cat /tmp/CORENAME 2>&1)  rbf: $(cat /tmp/RBFNAME 2>&1)"
	ps | grep -i '[M]iSTer'
	md5sum /media/fat/MiSTer /media/fat/MiSTer.clean /media/fat/MiSTer.prev /media/fat/MiSTer.stock 2>&1
} > $D/state.txt 2>&1
cat /proc/bus/input/devices > $D/input_devices.txt 2>&1
dmesg | tail -120 > $D/dmesg_tail.txt 2>&1
ls -la --time-style=full-iso /media/fat/config/inputs > $D/config_inputs_ls.txt 2>&1
ls -la --time-style=full-iso /media/fat/config /media/fat/_Utility /media/fat > $D/ls_misc.txt 2>&1
cp /tmp/guncal_apply.log /tmp/mister.log $D/ 2>/dev/null
cp /tmp/gundbg.csv /tmp/gundbg_out.csv $D/ 2>/dev/null
cp /media/fat/MiSTer.ini $D/ 2>/dev/null
cp /media/fat/config/GUNCAL* /media/fat/config/*.CFG $D/ 2>/dev/null
cd /tmp && tar cf - lc_collect | gzip -c
rm -rf $D

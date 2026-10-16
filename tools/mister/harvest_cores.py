#!/usr/bin/env python3
"""Load a list of arcade MRAs on the MiSTer one after another and record what the patched app logged for each core:
the framework's measured video, the picture edges the universal mapping derived, and the core's J/j button lists.

The MiSTer must be logged in on the console (see serial_run.py) and running a build with patches 0005..0008. The real gun
must be connected and bound: the mapping is applied from its reports. Each MRA is loaded, then given SETTLE seconds.

usage: harvest_cores.py <out file> <mra path on the MiSTer>...
"""
import re
import sys
import time

import serial_run

SETTLE = 45


def main():
	out_path = sys.argv[1]
	mras = sys.argv[2:]
	m = serial_run.Mister()
	with open(out_path, 'a', encoding='utf-8') as out:
		for mra in mras:
			counts = re.findall(r'^\s*(\d+)\s*$', m.run('grep -c "" /tmp/guncal_apply.log', 15), re.M)
			n0 = int(counts[-1]) if counts else 0
			m.run('echo "load_core %s" > /dev/MiSTer_cmd' % mra, 15)
			time.sleep(SETTLE)
			core = m.run('cat /tmp/CORENAME; echo; ps | grep "[M]iSTer /media" | sed "s/^ *[0-9]* root *//"', 20)
			log = m.run('tail -n +%d /tmp/guncal_apply.log' % (n0 + 1), 20)
			out.write('=== %s\n%s\n--- log\n%s\n\n' % (mra, core.strip(), log.strip()))
			out.flush()
			print('done', mra)


if __name__ == '__main__':
	main()

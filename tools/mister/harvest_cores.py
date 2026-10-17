#!/usr/bin/env python3
"""Load a list of cores on the MiSTer one after another and record what the patched app logged for each: the framework's
measured video, the picture edges the universal mapping derived, and the core's J/j button lists.

Give it arcade .mra files or core .rbf files, as absolute paths on the MiSTer. NEVER a ROM path: load_core treats whatever it
is given as a bitstream, and a ROM leaves the FPGA unconfigured and the app unable to start (the console then hangs on the
command FIFO). Loading a console's .rbf alone is enough for its video timing and button list.

The MiSTer must be logged in on the console (see serial_run.py) and running a build with patches 0005..0009. The real gun
must be connected and bound: the mapping is applied from its reports. Each core is given SETTLE seconds after loading.

usage: harvest_cores.py <out file> <path of an .mra or .rbf on the MiSTer>...
"""
import re
import sys
import time

import serial_run

SETTLE = 40

# A write to the command FIFO blocks for good when no app is reading it, which hangs the console: check the app is running and
# time the write out.
SEND = ('if ps | grep -q "[/]media/fat/MiSTer"; then '
        "timeout 8 sh -c 'echo \"load_core {path}\" > /dev/MiSTer_cmd' && echo SENT; "
        'else echo NOAPP; fi')


def main():
	out_path = sys.argv[1]
	paths = sys.argv[2:]
	for p in paths:
		if not p.lower().endswith(('.mra', '.rbf')):
			sys.exit('refusing %r: only .mra and .rbf can be loaded (a ROM would leave the FPGA unconfigured)' % p)

	m = serial_run.Mister()
	with open(out_path, 'a', encoding='utf-8') as out:
		for path in paths:
			counts = re.findall(r'^\s*(\d+)\s*$', m.run('grep -c "" /tmp/guncal_apply.log', 15), re.M)
			n0 = int(counts[-1]) if counts else 0
			sent = m.run(SEND.format(path=path), 25)
			if 'SENT' not in sent:
				out.write('=== %s\nNOT LOADED: %s\n\n' % (path, sent.strip()))
				print('not loaded', path)
				continue
			time.sleep(SETTLE)
			core = m.run('cat /tmp/CORENAME; echo; ps | grep "[/]media/fat/MiSTer" | sed "s/^ *[0-9]* root *//"', 20)
			log = m.run('tail -n +%d /tmp/guncal_apply.log' % (n0 + 1), 20)
			out.write('=== %s\n%s\n--- log\n%s\n\n' % (path, core.strip(), log.strip()))
			out.flush()
			print('done', path)


if __name__ == '__main__':
	main()

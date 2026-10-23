#!/usr/bin/env python3
"""On-device check that the probe stays off where it must (the menu, the GunCal core), run ON the MiSTer against a GUNDBG=1 build:
a virtual GunCon 2 (fakegun.py) pulls the trigger once on a lit spot, and its rows in /tmp/gundbg_out.csv must never leave probe phase 0.
usage: python3 fakegun_noprobe.py       (needs /tmp/fakegun.py next to it)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakegun

OUT = '/tmp/gundbg_out.csv'


def main():
	g = fakegun.FakeGun()
	time.sleep(4)
	t0 = int(time.time() * 1000) & 0xFFFFFFFF
	for i in range(5):
		g.report(611 + i, 150)
	g.trigger(True)
	for i in range(4):
		g.report(616, 151)
	g.trigger(False)
	for i in range(10):
		g.report(617, 151)
	time.sleep(0.3)
	g.close()
	rows = []
	for line in open(OUT).read().splitlines()[1:]:
		v = [int(x) for x in line.split(',')]
		if len(v) == 16 and v[1] >= t0:
			rows.append(v)
	dev = next((v[0] for v in rows if v[2] == 611), None)
	mine = [v for v in rows if v[0] == dev]
	pulled = any(v[4] for v in mine)
	probed = any(v[14] or v[15] for v in mine)
	core = open('/tmp/CORENAME').read().strip()
	ok = dev is not None and pulled and not probed
	print('%s core %s: pull seen %s, probe used %s' % ('ok  ' if ok else 'FAIL', core, pulled, probed))
	return 0 if ok else 1


if __name__ == '__main__':
	sys.exit(main())

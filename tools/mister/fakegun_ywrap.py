#!/usr/bin/env python3
"""On-device check of the Y-wrap bridge (CRTGUN_Y_WRAP in lightgun_crt.cpp), run ON the MiSTer against a GUNDBG=1 build
while a core whose picture reaches past line 255 is running (Terminator 2: picture to line 273).

A virtual GunCon 2 sends the Y values the kernel driver would deliver for lines 261 and 273 (5 and 17), for a middle line, for a
line just under the picture's top, and a dark report. The tracker's raw_y (/tmp/gundbg_out.csv) must show 261 and 273 for the first
two and be untouched for the rest. It tests the software only. Needs /tmp/fakegun.py next to it. usage: python3 fakegun_ywrap.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakegun

OUT = '/tmp/gundbg_out.csv'

# (raw x, driver's Y byte, expected raw_y in the tracker). x doubles as the row's tag; it changes each report so the kernel passes every one.
CASES = [
	(401, 5, 261, 'line 261, lit: wrapped, restored'),
	(402, 17, 273, 'line 273, lit: the last picture line, restored'),
	(403, 120, 120, 'middle of the screen: untouched'),
	(404, 24, 24, 'just under the picture top (ymin 22): untouched'),
	(405, 60, 60, 'a normal line: untouched'),
]


def main():
	g = fakegun.FakeGun()
	time.sleep(4)
	for x, y, _, _ in CASES:
		g.report(x, y)
		g.report(x + 20, 130)             # a different valid report in between
	g.report(0, 5)                        # no light: junk Y, left alone
	g.report(1, 5)
	time.sleep(2.5)                       # the app flushes its log once a second
	g.close()

	rows = {}
	for line in open(OUT).read().splitlines()[1:]:
		v = line.split(',')
		if len(v) >= 4:
			rows.setdefault(int(v[2]), []).append(int(v[3]))     # raw_x -> raw_y values seen

	bad = 0
	for x, y, want, what in CASES:
		got = rows.get(x, [])
		ok = want in got
		bad += 0 if ok else 1
		print('%-4s %-52s driver Y %3d -> expected %3d, tracker saw %s' % ('ok' if ok else 'FAIL', what, y, want, got[-3:]))
	print('FAILED' if bad else 'all ok')
	sys.exit(1 if bad else 0)


if __name__ == '__main__':
	main()

#!/usr/bin/env python3
"""End-to-end test of the GunCal calibration sequence, run ON the MiSTer while the GunCal core is running.

A virtual GunCon 2 shoots the five targets using an exact, made-up mapping (raw = a * px + b); the app must save
that mapping. The real gun must be quiet (unbound or untouched), otherwise its reports mix into the sequence.
The saved file is deleted at the end so a synthetic calibration never survives.

usage: python3 fakegun_cal.py        (needs /tmp/fakegun.py next to it)
"""
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakegun
from fakegun import BTN_X, EV_ABS, EV_KEY, EV_SYN, ABS_X, ABS_Y

AX, BX, AY, BY = 1.19, 112.0, 0.97, 18.0
W, H, MARGIN = 529, 240, 12
FILE = '/media/fat/config/GUNCAL_uni_0b9a_016a_v1.cfg'


def target(point):
	mx, my = W * MARGIN // 100, H * MARGIN // 100
	return [(W // 2, H // 2), (mx, my), (W - 1 - mx, my), (W - 1 - mx, H - 1 - my), (mx, H - 1 - my)][point]


def raw(px, py):
	return int(AX * px + BX + 0.5), int(AY * py + BY + 0.5)


def main():
	if os.path.exists(FILE):
		sys.exit('refusing to run: %s already exists (a real calibration?)' % FILE)
	g = fakegun.FakeGun()
	time.sleep(4)                                   # MiSTer notices the device
	try:
		g.report(0, 5)
		for k in range(5):
			x, y = raw(*target(k))
			g.report(x, y)                          # aiming at the target, nothing pulled yet
			g.report(x, y)
			g.trigger(True)
			for i in range(8):
				g.report(x + (i & 1), y)            # the flash: valid reports (1 unit of jitter)
			g.trigger(False)
			g.report(x, y)
			time.sleep(0.6)                         # past the 300 ms collection window
			print('shot %d done' % (k + 1))
		time.sleep(1.5)
		ok = os.path.exists(FILE)
		print('calibration file written:', ok)
		if ok:
			v = struct.unpack('<6i', open(FILE, 'rb').read(24))
			ax, bx, ay, by = v[1] / 1000.0, v[2] / 1000.0, v[3] / 1000.0, v[4] / 1000.0
			print('saved   : raw_x = %.4f*px + %.1f   raw_y = %.4f*py + %.1f' % (ax, bx, ay, by))
			print('expected: raw_x = %.4f*px + %.1f   raw_y = %.4f*py + %.1f' % (AX, BX, AY, BY))
			good = abs(ax - AX) < 0.03 and abs(bx - BX) < 3 and abs(ay - AY) < 0.03 and abs(by - BY) < 4
			print('PASS' if good else 'FAIL: saved mapping differs')
			return 0 if good else 1
		print('FAIL: nothing saved')
		return 1
	finally:
		g.close()
		if os.path.exists(FILE):
			os.remove(FILE)
			print('removed the synthetic calibration file')


if __name__ == '__main__':
	sys.exit(main())

#!/usr/bin/env python3
"""Integration test for the CRT lightgun tracker, run ON the MiSTer against a GUNDBG=1 build.

Creates a virtual evdev device that looks like a GunCon 2 (0b9a:016a, same axis ranges as the kernel
driver), plays scripted situations through MiSTer's real input path, then checks the tracker log
(/tmp/gundbg_out.csv). It tests the software wiring only; it says nothing about the physical gun.

usage: python3 fakegun.py
"""
import fcntl
import os
import random
import struct
import sys
import time

UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_ABSBIT = 0x40045564, 0x40045565, 0x40045567
UI_DEV_CREATE, UI_DEV_DESTROY = 0x5501, 0x5502
EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
ABS_X, ABS_Y, ABS_HAT0X, ABS_HAT0Y = 0, 1, 0x10, 0x11
BTN_A, BTN_B, BTN_X, BTN_Y, BTN_START, BTN_SELECT = 0x130, 0x131, 0x133, 0x134, 0x13b, 0x13a
EVENT = struct.Struct('llHHi')
STEP = 0.020          # one report every 20 ms, like the gun at 50 Hz
OUT = '/tmp/gundbg_out.csv'
XMIN, XMAX, YMIN, YMAX = 145, 700, 25, 245


class FakeGun:
	def __init__(self):
		self.fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
		for ev in (EV_KEY, EV_ABS):
			fcntl.ioctl(self.fd, UI_SET_EVBIT, ev)
		for k in (BTN_A, BTN_B, BTN_X, BTN_Y, BTN_START, BTN_SELECT):
			fcntl.ioctl(self.fd, UI_SET_KEYBIT, k)
		absmax, absmin = [0] * 64, [0] * 64
		for a, lo, hi in ((ABS_X, XMIN, XMAX), (ABS_Y, YMIN, YMAX), (ABS_HAT0X, -1, 1), (ABS_HAT0Y, -1, 1)):
			fcntl.ioctl(self.fd, UI_SET_ABSBIT, a)
			absmin[a], absmax[a] = lo, hi
		dev = struct.pack('<80sHHHHi', b'Namco GunCon 2', 3, 0x0b9a, 0x016a, 0x0100, 0)
		dev += struct.pack('<64i', *absmax) + struct.pack('<64i', *absmin) + struct.pack('<64i', *([0] * 64)) * 2
		os.write(self.fd, dev)
		fcntl.ioctl(self.fd, UI_DEV_CREATE)
		self.x = self.y = 0

	def _w(self, etype, code, value):
		os.write(self.fd, EVENT.pack(0, 0, etype, code, value))

	def report(self, x, y):
		self._w(EV_ABS, ABS_X, x)
		self._w(EV_ABS, ABS_Y, y)
		self._w(EV_SYN, 0, 0)
		time.sleep(STEP)

	def trigger(self, down):
		self._w(EV_KEY, BTN_X, 1 if down else 0)
		self._w(EV_SYN, 0, 0)

	def close(self):
		fcntl.ioctl(self.fd, UI_DEV_DESTROY)
		os.close(self.fd)


def run_scenario(g):
	"""Returns [(name, t_start_ms, t_end_ms)] using the wall clock (the same clock as input event times)."""
	phases = []
	t_ms = lambda: int(time.time() * 1000) & 0xFFFFFFFF   # MiSTer logs the low 32 bits

	def phase(name):
		time.sleep(0.03)            # keep the previous phase's last event (e.g. a trigger release) out of this window
		phases.append([name, t_ms(), None])

	def end():
		phases[-1][2] = t_ms()

	dark = lambda n: [g.report(i & 1, 5) for i in range(n)]      # lit-room noise: X toggles 0/1, Y stale

	phase('track'); [g.report(300 + i * 5, 130) for i in range(20)]; end()                      # x 300..395
	phase('dark_interior'); dark(15); end()                                                      # 300 ms
	phase('resume'); [g.report(400, 130) for _ in range(5)]; end()
	phase('dark_long'); dark(40); end()                                                          # 800 ms
	phase('edge_valid'); [g.report(695, 130) for _ in range(5)]; end()
	phase('edge_exit'); dark(5); end()
	phase('interior_again'); [g.report(300, 100) for _ in range(5)]; end()
	phase('shot_flash'); g.trigger(True); [g.report(300, 100) for _ in range(2)]
	dark(5)                                                                                      # black frame
	[g.report(310, 102) for _ in range(3)]                                                       # flash: real measurement
	dark(15); g.trigger(False); end()                                                            # 300 ms of dark after the flash
	phase('reload_shot'); [g.report(690, 130) for _ in range(5)]; dark(3); g.trigger(True); dark(10); g.trigger(False); end()
	phase('idle'); dark(10); end()
	return phases


def load_rows(t0, t1):
	rows = []
	for line in open(OUT).read().splitlines()[1:]:
		dev, t, rx, ry, trig, shot, ox, oy, off = (int(v) for v in line.split(','))
		if (t0 - 100) <= t <= (t1 + 100):
			rows.append((t, rx, ry, trig, shot, ox, oy, off))
	return rows


def main():
	g = FakeGun()
	time.sleep(4)                      # let MiSTer notice the new device
	t_start = int(time.time() * 1000) & 0xFFFFFFFF
	phases = run_scenario(g)
	time.sleep(2)                      # MiSTer flushes its log once a second
	g.close()
	rows = load_rows(t_start, int(time.time() * 1000) & 0xFFFFFFFF)
	print('tracker rows in test window: %d' % len(rows))
	if not rows:
		sys.exit('FAIL: MiSTer logged nothing - is this a GUNDBG=1 build and did it accept the virtual gun?')

	def within(name):
		p = next(p for p in phases if p[0] == name)
		# the phase end is taken after the last report's sleep, so stop 10 ms short of it: anything later
		# belongs to the next phase's first report
		return [r for r in rows if p[1] - 2 <= r[0] <= p[2] - 10], p

	fails = []

	def check(name, cond, detail=''):
		print('%-4s %s %s' % ('ok' if cond else 'FAIL', name, detail))
		if not cond:
			fails.append(name)

	r, _ = within('track')
	check('track passes raw through', bool(r) and all(x[7] == 0 and x[5] == x[1] for x in r if x[1] >= 16), '(%d rows)' % len(r))

	r, _ = within('dark_interior')
	check('interior dark gap holds last position', bool(r) and all(x[7] == 0 and x[5] == 395 and x[6] == 130 for x in r), str(r[:1]))

	r, p = within('dark_long')
	early = [x for x in r if x[0] <= p[1] + 450]
	late = [x for x in r if x[0] >= p[1] + 600]
	check('dark gap holds for ~dark_ms', bool(early) and all(x[7] == 0 for x in early))
	check('dark gap expires to offscreen', bool(late) and all(x[7] == 1 and x[5] < XMIN and x[6] < YMIN for x in late))

	r, _ = within('edge_exit')
	check('leaving through an edge is offscreen at once', bool(r) and all(x[7] == 1 for x in r if x[1] < 16))

	r, p = within('shot_flash')
	black = [x for x in r if x[1] < 16 and x[2] == 5][:5]
	check('shot window opened', any(x[4] == 1 for x in r))
	check('black frame after a shot holds the aim', bool(black) and all(x[7] == 0 and x[5] == 300 and x[6] == 100 for x in black), str(black[:1]))
	# one report arrives as X then Y events; the row between them pairs the new X with the old Y and is never delivered
	flash = [x for x in r if x[1] == 310 and x[2] == 102]
	check('flash measurement is taken', bool(flash) and all(x[5] == 310 and x[6] == 102 and x[7] == 0 for x in flash))
	after = [x for x in r if x[1] < 16 and x[0] > flash[-1][0]] if flash else []
	check('dark after the flash holds the flash position', bool(after) and all(x[7] == 0 and x[5] == 310 for x in after[:8]))

	r, _ = within('reload_shot')
	tail = [x for x in r if x[1] < 16]
	check('shot with no light stays offscreen', bool(tail) and all(x[7] == 1 and x[4] == 0 for x in tail), '(%d rows)' % len(tail))

	print('PASS' if not fails else 'FAILED: ' + ', '.join(fails))
	return 1 if fails else 0


if __name__ == '__main__':
	sys.exit(main())

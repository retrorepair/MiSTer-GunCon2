#!/usr/bin/env python3
"""On-device test of the probe (lightgun_crt.h, "Probe"), run ON the MiSTer against a GUNDBG=1 build, with any core but GunCal or the menu.

A virtual GunCon 2 (fakegun.py) shoots three times: in a dark scene where the only light is the flash that follows the probe press, in a
lit scene, and off the screen (no light at all). From /tmp/gundbg_out.csv (this device's rows) it checks what the app gave the core:
the aim off the screen and a probe press a few ms after the pull, the probe press up after 40 ms, the aim from the flash only once the
probe press is up, the real press 35 ms after that with the aim in place, and for the shot off the screen nothing but the probe press.
It tests the app on the MiSTer, not a game: whether a game takes the probe press as a reload is a matter for play.
The real gun may stay plugged in (its tracker is separate), but must not be fired during the test.

usage: python3 fakegun_probe.py       (needs /tmp/fakegun.py next to it)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakegun

OUT = '/tmp/gundbg_out.csv'
FIELD = 0.0167


def now_ms():
	return int(time.time() * 1000) & 0xFFFFFFFF


def rows(t0, dev):
	out = []
	for line in open(OUT).read().splitlines()[1:]:
		v = [int(x) for x in line.split(',')]
		if len(v) == 16 and v[1] >= t0 and (dev is None or v[0] == dev):
			out.append(dict(dev=v[0], t=v[1], rx=v[2], ry=v[3], trig=v[4], px=v[9], py=v[10], poff=v[11], ph=v[14], pr=v[15]))
	return out


def sequence(rs, t_pull):
	"""Times (ms after the pull) of: probe press, probe release, aim on the screen, real press, real release; and the aim."""
	ev = {}
	prev = None
	for r in rs:
		if r['t'] < t_pull:
			prev = r
			continue
		if prev is not None:
			if r['pr'] and not prev['pr']:
				ev.setdefault('probe_press' if 'probe_press' not in ev else 'real_press', r['t'] - t_pull)
			if prev['pr'] and not r['pr']:
				ev.setdefault('probe_release' if 'probe_release' not in ev else 'real_release', r['t'] - t_pull)
			if prev['poff'] and not r['poff'] and 'aim' not in ev:
				ev['aim'] = r['t'] - t_pull
				ev['aim_at'] = (r['px'], r['py'])
		prev = r
	return ev


def main():
	g = fakegun.FakeGun()
	time.sleep(4)                                           # the app finds the new device
	fails = []

	def check(name, cond, detail=''):
		print('%-4s %s %s' % ('ok' if cond else 'FAIL', name, detail))
		if not cond:
			fails.append(name)

	def rep(x, y, wait=FIELD):
		g._w(fakegun.EV_ABS, fakegun.ABS_X, x)
		g._w(fakegun.EV_ABS, fakegun.ABS_Y, y)
		g._w(fakegun.EV_SYN, 0, 0)
		time.sleep(wait)

	t_start = now_ms()
	for i in range(10):
		rep(401, 131)                                       # a unique place: finds this device's rows
	dev = next((r['dev'] for r in rows(t_start, None) if r['rx'] == 401), None)
	check('the app sees the virtual gun', dev is not None)
	if dev is None:
		g.close()
		return 1

	# 1. dark scene: nothing lit until the flash that answers the probe press (three fields after it)
	for i in range(8):
		rep(i & 1, 5)
	t1 = now_ms()
	g.trigger(True)
	for i in range(3):
		rep(i & 1, 5)
	rep(420, 135)                                           # the flash
	g.trigger(False)
	for i in range(12):
		rep(i & 1, 5)
	time.sleep(0.3)

	# 2. lit scene, the gun held perfectly still: after the pull it sends nothing (the kernel drops unchanged values), trigger held 100 ms
	for i in range(6):
		rep(500 + i, 180)
	t2 = now_ms()
	g.trigger(True)
	time.sleep(6 * FIELD)
	g.trigger(False)
	time.sleep(0.4)

	# 3. off the screen: no light at all
	for i in range(6):
		rep(i & 1, 5)
	t3 = now_ms()
	g.trigger(True)
	for i in range(4):
		rep(i & 1, 5)
	g.trigger(False)
	for i in range(14):
		rep(i & 1, 5)
	time.sleep(0.4)
	g.close()

	rs = rows(t_start, dev)
	s1 = sequence(rs, t1)
	print('dark scene:', s1)
	check('dark: probe press 3..12 ms after the pull', 3 <= s1.get('probe_press', -1) <= 12)
	check('dark: probe press lasts 40 ms', 40 <= s1.get('probe_release', 0) - s1.get('probe_press', 0) <= 50)
	check('dark: the aim is the flash', s1.get('aim_at') == (420, 135), str(s1.get('aim_at')))
	check('dark: the aim goes on only after the probe press is up', s1.get('aim', 0) >= s1.get('probe_release', 999))
	check('dark: real press 35 ms after the probe release, with the aim in place',
	      35 <= s1.get('real_press', 0) - s1.get('probe_release', 0) <= 45 and s1.get('real_press', 0) > s1.get('aim', 999))
	check('dark: the real press is released', 'real_release' in s1)

	check('dark: the real press lasts 40..50 ms (the trigger was already up)', 40 <= s1.get('real_release', 0) - s1.get('real_press', 0) <= 50)

	s2 = sequence(rs, t2)
	print('still gun: ', s2)
	check('still: the aim is where the still gun stands', s2.get('aim_at') == (505, 180), str(s2.get('aim_at')))
	check('still: the aim comes two fields + 8 ms after the probe press, once that press is up',
	      s2.get('aim', 0) >= s2.get('probe_release', 999) and s2.get('aim', 999) - s2.get('probe_press', 0) <= 60)
	check('still: real press given, and released after the trigger', 'real_press' in s2 and s2.get('real_release', 0) >= 100)

	s3 = sequence(rs, t3)
	print('off screen:', s3)
	check('off: only the probe press (it is the reload)', 'probe_press' in s3 and 'real_press' not in s3 and 'aim' not in s3)

	print('%d check(s) failed' % len(fails) if fails else 'all probe checks passed')
	return 1 if fails else 0


if __name__ == '__main__':
	sys.exit(main())

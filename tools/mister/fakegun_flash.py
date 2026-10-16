#!/usr/bin/env python3
"""On-device test of the aim-from-the-flash pointer (LIGHTGUN_CRT_MODE=1), run ON the MiSTer against a GUNDBG=1 build.

A virtual GunCon 2 wanders, then shoots three ways: with light at the aim, in the dark with the game's flash arriving
after the pull, and in the dark with no flash. The held aim (pub_x/pub_y/pub_off in /tmp/gundbg_out.csv) must be the
flash's median, must not follow the scene between pulls, and must be offscreen when there was no flash.
The real gun must be quiet (unbound), otherwise its reports mix in.

usage: python3 fakegun_flash.py       (needs /tmp/fakegun.py next to it)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakegun

OUT = '/tmp/gundbg_out.csv'


def now_ms():
	return int(time.time() * 1000) & 0xFFFFFFFF


def rows_since(t0):
	out = []
	for line in open(OUT).read().splitlines()[1:]:
		v = [int(x) for x in line.split(',')]
		if len(v) == 12 and v[1] >= t0:
			out.append(dict(t=v[1], rx=v[2], ry=v[3], trig=v[4], ox=v[6], oy=v[7], off=v[8], px=v[9], py=v[10], poff=v[11]))
	return out


def main():
	g = fakegun.FakeGun()
	time.sleep(4)
	marks = {}
	fails = []

	def check(name, cond, detail=''):
		print('%-4s %s %s' % ('ok' if cond else 'FAIL', name, detail))
		if not cond:
			fails.append(name)

	def mark(name):
		time.sleep(0.03)
		marks[name] = now_ms()

	dark = lambda n: [g.report(i & 1, 5) for i in range(n)]

	mark('wander')
	for i in range(15):
		g.report(300 + i * 6, 130)
	mark('wander_end')

	mark('lit_pull')
	g.report(320, 110); g.report(320, 110)
	g.trigger(True)
	dark(3)                                   # the black frames
	g.report(330, 112); g.report(331, 113); g.report(329, 111)      # the flash
	for i in range(8):
		g.report(500 + i * 3, 200)            # the scene afterwards
	g.trigger(False)
	mark('lit_pull_end')

	mark('dark_pull')
	dark(30)
	g.trigger(True)
	dark(3)
	g.report(250, 120); g.report(252, 121); g.report(248, 119)
	dark(10)
	g.report(600, 60)
	g.trigger(False)
	mark('dark_pull_end')

	mark('no_flash')
	dark(45)                                  # long enough that the last mid-screen reading is no longer held
	g.trigger(True)
	dark(30)                                  # 600 ms with no light at all
	g.trigger(False)
	mark('no_flash_end')

	time.sleep(1.5)
	g.close()

	def phase(a, b):
		return [r for r in rows_since(marks[a]) if r['t'] <= marks[b]]

	w = phase('wander', 'wander_end')
	check('no pull: the held aim does not follow the gun', bool(w) and len({(r['px'], r['py']) for r in w}) == 1, '(%d rows, aim %s)' % (len(w), (w[0]['px'], w[0]['py']) if w else None))

	r = phase('lit_pull', 'lit_pull_end')
	check('pull with light: aim starts at the gun position', any(x['trig'] and x['px'] == 320 and x['py'] == 110 for x in r))
	check('pull with light: aim becomes the flash median', r and (r[-1]['px'], r[-1]['py'], r[-1]['poff']) == (330, 112, 0), str((r[-1]['px'], r[-1]['py'], r[-1]['poff'])) if r else '')
	check('pull with light: the scene afterwards does not move it', all((x['px'], x['py']) == (330, 112) for x in r[-6:]))

	r = phase('dark_pull', 'dark_pull_end')
	press = [x for x in r if x['trig']]
	check('pull in the dark: offscreen until the flash', bool(press) and press[0]['poff'] == 1)
	check('pull in the dark: the flash sets the aim', r and (r[-1]['px'], r[-1]['py'], r[-1]['poff']) == (250, 120, 0), str((r[-1]['px'], r[-1]['py'], r[-1]['poff'])) if r else '')

	r = phase('no_flash', 'no_flash_end')
	check('pull with no flash: stays offscreen', bool(r) and all(x['poff'] == 1 for x in r if x['trig']))

	print('PASS' if not fails else 'FAILED: ' + ', '.join(fails))
	return 1 if fails else 0


if __name__ == '__main__':
	sys.exit(main())

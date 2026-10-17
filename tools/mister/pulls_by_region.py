#!/usr/bin/env python3
"""For every trigger pull in /tmp/gundbg_out.csv (run ON the MiSTer, GUNDBG=1 build): where was the gun pointing just before it (the last
report with light in the 400 ms before), and did the pull end with a held aim on the screen or offscreen (no flash seen)?

Counts the pulls per sixth of the assumed picture width and height, so a region where pulls keep ending offscreen shows up as a dead zone.
usage: python3 pulls_by_region.py
"""
import re

OUT = '/tmp/gundbg_out.csv'
LOG = '/tmp/guncal_apply.log'
VALID = 16
LOOKBACK = 400      # ms
WINDOW = 450        # ms after the pull in which the flash is looked for

assumed = None
for line in open(LOG):
	m = re.search(r'picture .* raw x (\d+)\.\.(\d+), y (\d+)\.\.(\d+)', line)
	if m:
		assumed = [int(g) for g in m.groups()]
x0, x1, y0, y1 = assumed
rows = []
for line in open(OUT).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		rows.append((int(f[1]), int(f[2]), int(f[3]), int(f[4]), int(f[11]), int(f[9]), int(f[10])))   # t, rx, ry, trig, pub_off, pub_x, pub_y

NB = 6
bx = [[0, 0] for _ in range(NB)]     # [on, off] by x sixth
by = [[0, 0] for _ in range(NB)]
nolast = [0, 0]
prev = 0
for i, (t, rx, ry, trig, poff, px, py) in enumerate(rows):
	if trig and not prev:
		# last report with light shortly before
		last = None
		for j in range(i, max(-1, i - 400), -1):
			if t - rows[j][0] > LOOKBACK:
				break
			if rows[j][1] >= VALID:
				last = rows[j]
				break
		# the held aim at the end of the flash window
		end = i
		while end + 1 < len(rows) and rows[end + 1][0] - t <= WINDOW:
			end += 1
		off = rows[end][4]
		if last is None:
			nolast[off] += 1
		else:
			ix = min(NB - 1, max(0, (last[1] - x0) * NB // (x1 - x0 + 1)))
			iy = min(NB - 1, max(0, (last[2] - y0) * NB // (y1 - y0 + 1)))
			bx[ix][off] += 1
			by[iy][off] += 1
	prev = trig

print('assumed picture x %d..%d y %d..%d; pulls by where the gun last saw light (400 ms before)' % (x0, x1, y0, y1))
print('no light in the 400 ms before: on-screen aim %d, offscreen %d' % (nolast[0], nolast[1]))
for name, b, lo, hi in (('X', bx, x0, x1), ('Y', by, y0, y1)):
	print(name + ' sixth      raw range      pulls  ended on-screen  ended offscreen')
	for k in range(NB):
		a = lo + k * (hi - lo + 1) // NB
		z = lo + (k + 1) * (hi - lo + 1) // NB - 1
		n = sum(b[k])
		print('  %d   %4d..%-4d   %5d   %8d         %8d' % (k + 1, a, z, n, b[k][0], b[k][1]))

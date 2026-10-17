#!/usr/bin/env python3
"""Where does the lit picture end? Run ON the MiSTer against /tmp/gundbg_out.csv from a GUNDBG=1 session.

Each time the gun loses light (a valid report followed by a no-light one), the last position it saw is a place where light ended: an
edge of the lit picture, or a dark area. Swept off the screen, these pile up at the real edges. Prints histograms of those last
positions in bins of 10 raw units, and the assumed edges for comparison.

usage: python3 light_edges.py
"""
import re

OUT = '/tmp/gundbg_out.csv'
LOG = '/tmp/guncal_apply.log'
VALID = 16

assumed = None
for line in open(LOG):
	m = re.search(r'picture .* raw x (\d+)\.\.(\d+), y (\d+)\.\.(\d+)', line)
	if m:
		assumed = [int(g) for g in m.groups()]

last = None
ends = []
for line in open(OUT).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) < 12:
		continue
	rx, ry = int(f[2]), int(f[3])
	if rx >= VALID:
		last = (rx, ry)
	elif last is not None:
		ends.append(last)
		last = None

print('light lost %d times; assumed picture x %d..%d y %d..%d' % (len(ends), assumed[0], assumed[1], assumed[2], assumed[3]))


def hist(vals, lo, hi, step, mark_lo, mark_hi):
	bins = {}
	for v in vals:
		if lo <= v < hi:
			bins[v // step * step] = bins.get(v // step * step, 0) + 1
	top = max(bins.values()) if bins else 1
	for b in range(lo // step * step, hi, step):
		n = bins.get(b, 0)
		tag = ''
		if b <= mark_lo < b + step:
			tag = '  <-- assumed low edge'
		if b <= mark_hi < b + step:
			tag = '  <-- assumed high edge'
		print('  %4d..%-4d %5d %s%s' % (b, b + step - 1, n, '#' * int(40.0 * n / top), tag))


print('raw X where light ended:')
hist([e[0] for e in ends], 40, 800, 20, assumed[0], assumed[1])
print('raw Y where light ended:')
hist([e[1] for e in ends], 0, 260, 10, assumed[2], assumed[3])

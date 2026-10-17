#!/usr/bin/env python3
"""Where did the gun actually see light? Run ON the MiSTer against /tmp/gundbg_out.csv from a GUNDBG=1 session.

Prints percentiles of the raw X and Y of every report with light (X >= 16), and the edges the app assumed for the core (the last
'picture' line of /tmp/guncal_apply.log). If the player swept the gun to the edges of the visible picture, the extremes of what the gun
saw are the real picture edges in raw units: compare them with the assumed ones.

usage: python3 edge_stats.py [min_x_valid]
"""
import re
import sys

OUT = '/tmp/gundbg_out.csv'
LOG = '/tmp/guncal_apply.log'
valid_min = int(sys.argv[1]) if len(sys.argv) > 1 else 16


def pct(v, p):
	return v[min(len(v) - 1, int(len(v) * p / 100.0))]


xs, ys, shots = [], [], []
prev_trig = 0
rows = open(OUT).read().splitlines()[1:]
for line in rows:
	f = line.split(',')
	if len(f) < 12:
		continue
	rx, ry, trig = int(f[2]), int(f[3]), int(f[4])
	if rx >= valid_min:
		xs.append(rx)
		ys.append(ry)
	if trig and not prev_trig:
		shots.append((int(f[9]), int(f[10]), int(f[11]), rx, ry))
	prev_trig = trig

print('rows %d, with light %d (%.0f%%)' % (len(rows), len(xs), 100.0 * len(xs) / max(1, len(rows))))
if xs:
	xs.sort()
	ys.sort()
	for name, v in (('raw X', xs), ('raw Y', ys)):
		print('%s with light: min %d  1%% %d  5%% %d  50%% %d  95%% %d  99%% %d  max %d' %
		      (name, v[0], pct(v, 1), pct(v, 5), pct(v, 50), pct(v, 95), pct(v, 99), v[-1]))

assumed = None
for line in open(LOG):
	m = re.search(r'picture .* raw x (\d+)\.\.(\d+), y (\d+)\.\.(\d+)', line)
	if m:
		assumed = [int(g) for g in m.groups()]
if assumed:
	print('assumed picture edges: x %d..%d  y %d..%d' % tuple(assumed))

if shots:
	off = sum(1 for s in shots if s[2])
	print('trigger pulls %d, of which the held aim was offscreen %d' % (len(shots), off))
	lit = [s for s in shots if not s[2]]
	if lit:
		px = sorted(s[0] for s in lit)
		py = sorted(s[1] for s in lit)
		print('held aim of the on-screen pulls: x min %d median %d max %d | y min %d median %d max %d' % (px[0], px[len(px) // 2], px[-1], py[0], py[len(py) // 2], py[-1]))

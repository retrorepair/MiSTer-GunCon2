#!/usr/bin/env python3
"""Extremes and resting positions from a GUNDBG trace (runs on the PC or the MiSTer).

  python tools/analyze_ranges.py captures/gundbg.csv
"""
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_gundbg as a

rows = a.load_raw(sys.argv[1])
v = [r for r in rows if r[1] >= a.X_VALID_MIN]
xs = sorted(r[1] for r in v)
ys = sorted(r[2] for r in v)


def pc(vals, p):
	return vals[min(len(vals) - 1, int(len(vals) * p))]


print('valid reports', len(v), 'of', len(rows))
print('X percentiles 0.5/2/10/50/90/98/99.5:', [pc(xs, p) for p in (.005, .02, .1, .5, .9, .98, .995)])
print('Y percentiles 0.5/2/10/50/90/98/99.5:', [pc(ys, p) for p in (.005, .02, .1, .5, .9, .98, .995)])
print('X min/max', xs[0], xs[-1], ' Y min/max', ys[0], ys[-1])

runs, cur = [], []
for r in rows:
	if r[1] >= a.X_VALID_MIN:
		cur.append(r)
	else:
		if len(cur) >= 15:
			runs.append(cur)
		cur = []
if len(cur) >= 15:
	runs.append(cur)
print('long valid runs (>=15 reports):', len(runs))
for c in runs[:60]:
	print('  n=%3d  x %4d..%4d (med %4d)  y %3d..%3d (med %3d)' % (
		len(c), min(r[1] for r in c), max(r[1] for r in c), statistics.median(r[1] for r in c),
		min(r[2] for r in c), max(r[2] for r in c), statistics.median(r[2] for r in c)))

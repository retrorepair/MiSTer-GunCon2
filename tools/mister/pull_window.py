#!/usr/bin/env python3
"""Print the tracker's rows around chosen trigger pulls of /tmp/gundbg_out.csv (run ON the MiSTer): what the gun saw (raw), whether the
trigger was down, the aim the tracker held (pub) and whether it was offscreen, every STEP ms from BEFORE ms before to AFTER ms after.
usage: python3 pull_window.py <pull numbers...>   (numbers as in pull_table.py)"""
import sys
import os
CSV = os.environ.get('CSV', '/tmp/gundbg_out.csv')
BEFORE, AFTER, STEP = int(os.environ.get('BEFORE', 500)), int(os.environ.get('AFTER', 900)), int(os.environ.get('STEP', 30))
rows = []
for line in open(CSV).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		try:
			rows.append([int(v) for v in f[:12]])
		except ValueError:
			pass
pulls = [i for i in range(1, len(rows)) if rows[i][4] == 1 and rows[i - 1][4] == 0]
for n in [int(a) for a in sys.argv[1:]]:
	i = pulls[n]
	t0 = rows[i][1]
	print('--- pull %d at %d' % (n, t0))
	print('  dt   rawX rawY trig shot | out_x out_y off | pub_x pub_y pub_off')
	last = -10 ** 9
	for r in rows:
		dt = r[1] - t0
		if dt < -BEFORE or dt > AFTER:
			continue
		if dt - last < STEP and not (r[4] != 0 and dt >= -STEP and dt <= STEP):
			continue
		last = dt
		print('%5d  %5d %4d  %d    %d   | %5d %4d  %d  | %5d %4d  %d' % (dt, r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]))

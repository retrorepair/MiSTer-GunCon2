#!/usr/bin/env python3
"""Pulls made with NO light on the gun (aimed at the floor, a dark patch, off the screen): what did the tracker decide at that instant?
(run ON the MiSTer against a GUNDBG=1 trace). For each: how long the gun had been dark, where it last saw light, and whether the aim
handed to the core at the pull (pub) was OFFSCREEN or a held on-screen position. A reload needs OFFSCREEN at the pull.
usage: python3 dark_pulls.py <csv>"""
import sys
rows = []
for line in open(sys.argv[1]).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		try:
			rows.append([int(v) for v in f[:12]])
		except ValueError:
			pass
pulls = [i for i in range(1, len(rows)) if rows[i][4] == 1 and rows[i - 1][4] == 0]
print('pull   t_ms      dark_for  last light X,Y     at the pull: out(off?)  pub(off?)   verdict')
for n, i in enumerate(pulls):
	r = rows[i]
	if r[2] >= 16:
		continue
	j = i
	while j > 0 and rows[j][2] < 16:
		j -= 1
	dark = r[1] - rows[j][1] if rows[j][2] >= 16 else 99999
	lx, ly = rows[j][2], rows[j][3]
	verdict = 'RELOAD OK (offscreen at the pull)' if r[11] else 'NOT offscreen at the pull -> a shot, no reload'
	print('%3d %9d  %7d ms  %4d,%-4d            %d (%d)          %d (%d)      %s' % (n, r[1] % 10000000, dark, lx, ly, r[8], r[8], r[11], r[11], verdict))

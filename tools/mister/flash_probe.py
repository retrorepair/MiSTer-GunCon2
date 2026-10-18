#!/usr/bin/env python3
"""Does the gun see the game's flash where it is aimed? (run ON the MiSTer against /tmp/gundbg_out.csv, or a copy)

For every trigger pull: how much light the gun saw in the 300 ms BEFORE (the scene itself), how soon the first light came AFTER the pull
and how much light there was in the 300 ms after (the flash, on top of the scene), and where (raw X / Y). Pulls are grouped into sets
where the gap to the next pull is under GAP ms. A flash that lights where the gun is aimed shows up as light after the pull in a place that
was dark before it.
usage: python3 flash_probe.py [csv]"""
import sys
CSV = sys.argv[1] if len(sys.argv) > 1 else '/tmp/gundbg_out.csv'
VALID, WIN, GAP = 16, 300, 2500
rows = []
for line in open(CSV).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		try:
			rows.append([int(v) for v in f[:12]])
		except ValueError:
			pass
pulls = [i for i in range(1, len(rows)) if rows[i][4] == 1 and rows[i - 1][4] == 0]
print('pulls %d' % len(pulls))
print(' set   t_s   before: lit%% meanX meanY | after: lit%% first-light-ms  meanX meanY | verdict')
s = 0
prev = None
for k, i in enumerate(pulls):
	t = rows[i][1]
	if prev is not None and t - prev > GAP:
		s += 1
	prev = t
	b = [r for r in rows[:i] if t - WIN <= r[1] < t]
	a = [r for r in rows[i:] if r[1] <= t + WIN]
	bl = [r for r in b if r[2] >= VALID]
	al = [r for r in a if r[2] >= VALID]
	bp = 100 * len(bl) // len(b) if b else 0
	ap = 100 * len(al) // len(a) if a else 0
	first = (al[0][1] - t) if al else -1
	bx = sum(r[2] for r in bl) // len(bl) if bl else 0
	by = sum(r[3] for r in bl) // len(bl) if bl else 0
	ax = sum(r[2] for r in al) // len(al) if al else 0
	ay = sum(r[3] for r in al) // len(al) if al else 0
	if bp < 30 and ap >= 30: v = 'FLASH SEEN (dark before, lit after)'
	elif bp < 30 and ap < 30: v = 'NO LIGHT either side'
	elif bp >= 30 and ap >= 30: v = 'lit before and after (scene lit)'
	else: v = 'light LOST after the pull'
	print('%3d %7.1f   %3d %5d %4d        |        %3d %6d       %5d %4d | %s' % (s, (t % 1000000) / 1000.0, bp, bx, by, ap, first, ax, ay, v))

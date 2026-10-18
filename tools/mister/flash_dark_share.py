#!/usr/bin/env python3
"""Of the pulls made with light on the gun, how many see a DARK frame during the flash (the gun's spot is black) and how many stay lit
through it (the spot is on something the flash draws bright, e.g. a white target box)? (run ON the MiSTer, or on a copy of a trace)
usage: python3 flash_dark_share.py <csv>"""
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
dark = lit = skipped = 0
litlist = []
for i in pulls:
	t = rows[i][1]
	if rows[i][2] < 16:
		skipped += 1
		continue
	win = [r for r in rows[i:] if 10 <= r[1] - t <= 110]
	if not win:
		skipped += 1
		continue
	if any(r[2] < 16 for r in win):
		dark += 1
	else:
		lit += 1
		litlist.append((rows[i][2], rows[i][3], len(win)))
print('pulls %d: skipped (no light at the pull) %d' % (len(pulls), skipped))
print('with light at the pull: DARK during the flash %d, STAYED LIT through the flash %d' % (dark, lit))
for x, y, n in litlist[:20]:
	print('  lit through the flash at aim %d,%d (%d readings in 10..110 ms)' % (x, y, n))

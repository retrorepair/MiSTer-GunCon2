#!/usr/bin/env python3
"""What does the game's flash look like to the gun? For each pull made while the gun was lit: the readings from the first DARK report
after the pull until the scene is lit again (the flash), listed as X,Y, with the aim before the pull for comparison.
(run ON the MiSTer, or on a copy of a GUNDBG=1 trace)  usage: python3 flash_shape.py <csv> [count]"""
import sys
rows = []
for line in open(sys.argv[1]).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		try:
			rows.append([int(v) for v in f[:12]])
		except ValueError:
			pass
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 12
pulls = [i for i in range(1, len(rows)) if rows[i][4] == 1 and rows[i - 1][4] == 0]
shown = 0
dy = []
for i in pulls:
	if rows[i][2] < 16:
		continue
	t = rows[i][1]
	ax, ay = rows[i][2], rows[i][3]
	seq = [r for r in rows[i:] if r[1] <= t + 330]
	k = next((n for n, r in enumerate(seq) if r[2] < 16), None)
	if k is None:
		continue
	out, last = [], None
	for r in seq[k:]:
		tag = ('%d,%d' % (r[2], r[3])) if r[2] >= 16 else 'dark'
		if tag != last:
			out.append('%s@%d' % (tag, r[1] - t))
			last = tag
		if r[2] >= 16 and r[3] != 5:
			dy.append(ay - r[3])
	if shown < limit:
		print('aim %d,%d  flash: %s' % (ax, ay, ' '.join(out[:14])))
		shown += 1
if dy:
	dy.sort()
	print('aim Y minus Y of the lit readings during the flash (not counting Y=5): n %d  min %d  median %d  max %d' % (len(dy), dy[0], dy[len(dy) // 2], dy[-1]))

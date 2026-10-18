#!/usr/bin/env python3
"""Readings that cannot be a real aim: the gun reports light (X >= 16) but Y is above the top of the picture or below its bottom.
How many are there, and are they right after trigger pulls (the game's flash)? (run ON the MiSTer, or on a copy of the trace)
usage: python3 junk_y.py <csv> [ymin ymax]   (defaults 18 254: the Model 2 filled picture)"""
import bisect, collections, sys
csv = sys.argv[1]
ymin = int(sys.argv[2]) if len(sys.argv) > 2 else 18
ymax = int(sys.argv[3]) if len(sys.argv) > 3 else 254
rows = []
for line in open(csv).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		try:
			rows.append([int(v) for v in f[:12]])
		except ValueError:
			pass
pulls = [rows[i][1] for i in range(1, len(rows)) if rows[i][4] == 1 and rows[i - 1][4] == 0]
lit = [r for r in rows if r[2] >= 16]
junk = [r for r in lit if r[3] < ymin - 5 or r[3] > ymax + 5]


def since(t):
	k = bisect.bisect_right(pulls, t) - 1
	return t - pulls[k] if k >= 0 else 10 ** 9


after = [r for r in lit if since(r[1]) <= 400]
ja = [r for r in junk if since(r[1]) <= 400]
print('pulls %d; lit readings %d; Y outside the picture (%d..%d +-5): %d (%.1f%%)' % (len(pulls), len(lit), ymin, ymax, len(junk), 100.0 * len(junk) / max(1, len(lit))))
print('within 400 ms after a pull: lit %d, of which outside %d (%.1f%%); elsewhere: lit %d, outside %d (%.1f%%)' % (
	len(after), len(ja), 100.0 * len(ja) / max(1, len(after)),
	len(lit) - len(after), len(junk) - len(ja), 100.0 * (len(junk) - len(ja)) / max(1, len(lit) - len(after))))
print('values:', sorted(collections.Counter(r[3] for r in junk).items())[:14])
if junk:
	xs = sorted(r[2] for r in junk)
	print('X of those: min %d median %d max %d' % (xs[0], xs[len(xs) // 2], xs[-1]))

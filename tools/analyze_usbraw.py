#!/usr/bin/env python3
"""Summarise a raw GunCon 2 report log written by tools/mister/usbraw.py.

  python tools/analyze_usbraw.py captures/lit_usbraw.log      (also runs on the MiSTer)

Each line is "<seconds> <urb status> <6 byte report as hex>": buttons (u16, active low), X (u16), Y (u16).
"""
import collections
import statistics
import sys

X_VALID_MIN = 16


def load(path):
	rows = []
	for line in open(path):
		t, st, h = line.split()
		b = bytes.fromhex(h)
		if len(b) == 6:
			rows.append((float(t), (b[0] << 8) | b[1], b[2] | (b[3] << 8), b[4] | (b[5] << 8)))
	return rows


def bucket(vals, size, cap):
	c = collections.Counter(min(v // size, cap) * size for v in vals)
	return sorted(c.items())


def main(path):
	rows = load(path)
	print('reports: %d over %.1f s' % (len(rows), rows[-1][0] - rows[0][0]))
	gaps = [(rows[i + 1][0] - rows[i][0]) * 1000 for i in range(len(rows) - 1)]
	print('gap ms: median %.1f  p90 %.1f  max %.1f' % (statistics.median(gaps), sorted(gaps)[int(len(gaps) * .9)], max(gaps)))
	valid = [r for r in rows if r[2] >= X_VALID_MIN]
	print('X >= %d: %d of %d (%.0f%%)' % (X_VALID_MIN, len(valid), len(rows), 100.0 * len(valid) / len(rows)))
	pulls = sum(1 for i in range(1, len(rows)) if not (rows[i][1] & 0x2000) and (rows[i - 1][1] & 0x2000))
	print('trigger pulls in this capture: %d' % pulls)
	if valid:
		xs, ys = [r[2] for r in valid], [r[3] for r in valid]
		print('valid x %d..%d median %d | y %d..%d median %d' % (min(xs), max(xs), statistics.median(xs), min(ys), max(ys), statistics.median(ys)))
		inbox = [r for r in valid if 145 <= r[2] <= 700 and 25 <= r[3] <= 245]
		print('inside the default screen box: %d of %d (%.0f%%)' % (len(inbox), len(valid), 100.0 * len(inbox) / len(valid)))
		print('X histogram/100:', bucket(xs, 100, 12))
		print('Y histogram/20: ', bucket(ys, 20, 20))
	# consecutive valid reports are what a locked gun produces while aimed at the picture
	runs, cur = [], 0
	for r in rows:
		if r[2] >= X_VALID_MIN:
			cur += 1
		else:
			if cur:
				runs.append(cur)
			cur = 0
	if cur:
		runs.append(cur)
	if runs:
		print('valid run lengths: median %d  max %d  (runs: %d)' % (statistics.median(runs), max(runs), len(runs)))
	# a gun locked to the CRT's sync, aimed at one spot, repeats nearly the same X/Y every frame (a few units);
	# a gun with no usable sync reference reports unrelated numbers every time
	pairs = [(rows[i], rows[i + 1]) for i in range(len(rows) - 1) if rows[i][2] >= X_VALID_MIN and rows[i + 1][2] >= X_VALID_MIN]
	if pairs:
		dx = sorted(abs(b[2] - a[2]) for a, b in pairs)
		dy = sorted(abs(b[3] - a[3]) for a, b in pairs)
		print('jump between consecutive valid reports: median dx %d dy %d | p90 dx %d dy %d  (locked and still: single digits)' % (
			dx[len(dx) // 2], dy[len(dy) // 2], dx[int(len(dx) * .9)], dy[int(len(dy) * .9)]))
		small = sum(1 for a, b in pairs if abs(b[2] - a[2]) <= 8 and abs(b[3] - a[3]) <= 8)
		print('pairs within 8 units in both axes: %d of %d (%.0f%%)' % (small, len(pairs), 100.0 * small / len(pairs)))
	for lo, hi, name in ((0, 8, 'first 8 s'), (8, 18, 'sweep 8-18 s'), (18, 26, 'last 7 s')):
		seg = [r for r in rows if lo <= r[0] < hi]
		sv = [r for r in seg if r[2] >= X_VALID_MIN]
		print('%-13s %4d reports, %4d with light' % (name, len(seg), len(sv)))


if __name__ == '__main__':
	main(sys.argv[1])

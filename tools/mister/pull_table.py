#!/usr/bin/env python3
"""One line per trigger pull of a GUNDBG=1 session (run ON the MiSTer, or anywhere with a copy of /tmp/gundbg_out.csv).

For each pull (trigger down): where the gun was just before it (the last report with light in the 600 ms before, raw units), what the
tracker had as the aim a moment after the pull, and what it finally held when the flash window had closed (pub_x / pub_y, and whether
that was OFFSCREEN). Then the same positions as a fraction of the picture the app assumed (the last 'tracker edges' line of
/tmp/guncal_apply.log), and a histogram of where the gun saw light. Meant to answer: aimed HERE, what did the core get?

usage: python3 pull_table.py [csv] [log]
"""
import re
import sys

CSV = sys.argv[1] if len(sys.argv) > 1 else '/tmp/gundbg_out.csv'
LOG = sys.argv[2] if len(sys.argv) > 2 else '/tmp/guncal_apply.log'
VALID = 16
LOOK = 600     # ms before a pull in which the gun's last light is looked for
HOLD = 600     # ms after a pull at which the held aim is read

edges = None
inset = None
for line in open(LOG):
	m = re.search(r'tracker edges x (\d+)\.\.(\d+) y (\d+)\.\.(\d+), on-screen aims kept within x (\d+)\.\.(\d+) y (\d+)\.\.(\d+)', line)
	if m:
		g = [int(v) for v in m.groups()]
		edges, inset = g[:4], g[4:]
x0, x1, y0, y1 = edges
print('tracker edges x %d..%d y %d..%d; aims kept within x %d..%d y %d..%d' % (x0, x1, y0, y1, inset[0], inset[1], inset[2], inset[3]))

rows = []
for line in open(CSV).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		try:
			rows.append([int(v) for v in f[:12]])
		except ValueError:
			pass
# columns: dev t_ms raw_x raw_y trig shot out_x out_y off pub_x pub_y pub_off
lit = [r for r in rows if r[2] >= VALID]
print('rows %d, with light %d' % (len(rows), len(lit)))
if lit:
	xs = sorted(r[2] for r in lit)
	ys = sorted(r[3] for r in lit)
	pc = lambda v, p: v[min(len(v) - 1, len(v) * p // 100)]
	print('light X: min %d 1%% %d 10%% %d 50%% %d 90%% %d 99%% %d max %d' % (xs[0], pc(xs, 1), pc(xs, 10), pc(xs, 50), pc(xs, 90), pc(xs, 99), xs[-1]))
	print('light Y: min %d 1%% %d 10%% %d 50%% %d 90%% %d 99%% %d max %d' % (ys[0], pc(ys, 1), pc(ys, 10), pc(ys, 50), pc(ys, 90), pc(ys, 99), ys[-1]))

pulls = [i for i in range(1, len(rows)) if rows[i][4] == 1 and rows[i - 1][4] == 0]
print('pulls %d' % len(pulls))
print(' #   t_ms   aimX  aimY  (fx   fy )   held X  Y   (fx   fy )  offscreen  flash-readings')
for n, i in enumerate(pulls):
	t = rows[i][1]
	before = [r for r in rows[:i] if r[1] >= t - LOOK and r[2] >= VALID]
	ax, ay = (before[-1][2], before[-1][3]) if before else (None, None)
	nxt = rows[pulls[n + 1]][1] if n + 1 < len(pulls) else 10 ** 12
	after = [r for r in rows[i:] if r[1] <= t + HOLD and r[1] < nxt]       # not into the next pull's own decision
	held = after[-1] if after else rows[i]
	flash = sum(1 for r in after if r[2] >= VALID)
	fa = ('%.2f %.2f' % ((ax - x0) / (x1 - x0), (ay - y0) / (y1 - y0))) if ax is not None else '  -    -  '
	fh = '%.2f %.2f' % ((held[9] - x0) / (x1 - x0), (held[10] - y0) / (y1 - y0))
	print('%2d %7d  %5s %5s  (%s)  %5d %4d  (%s)   %s       %d' % (n, t % 10000000, ax if ax is not None else '-', ay if ay is not None else '-', fa, held[9], held[10], fh, 'OFF' if held[11] else 'on ', flash))

tab = {}
for n, i in enumerate(pulls):
	t = rows[i][1]
	before = [r for r in rows[:i] if r[1] >= t - LOOK and r[2] >= VALID]
	if not before:
		continue
	nxt = rows[pulls[n + 1]][1] if n + 1 < len(pulls) else 10 ** 12
	after = [r for r in rows[i:] if r[1] <= t + HOLD and r[1] < nxt]
	held = after[-1] if after else rows[i]
	b = max(0, min(9, int((before[-1][2] - x0) * 10 / (x1 - x0))))
	c = tab.setdefault(b, [0, 0, 0, 0])
	c[1 if held[11] else 0] += 1
	c[2] += 1
	c[3] += 1 if sum(1 for r in after if r[2] >= VALID) >= 3 else 0
print('pulls that had light just before them, by tenth of the picture width: held ON / OFF, and how many saw a flash (3+ readings after the pull)')
print('  ' + '  '.join('%d: on %d off %d flash %d/%d' % (b, tab[b][0], tab[b][1], tab[b][3], tab[b][2]) for b in sorted(tab)))
print('light seen, by tenth of the picture width (raw %d..%d):' % (x0, x1))
bins = [0] * 12
for r in lit:
	b = int((r[2] - x0) * 10 / (x1 - x0)) + 1
	bins[max(0, min(11, b))] += 1
print('  below  ' + ' '.join('%5d' % v for v in bins[:1]) + '  tenths ' + ' '.join('%5d' % v for v in bins[1:11]) + '  above %5d' % bins[11])

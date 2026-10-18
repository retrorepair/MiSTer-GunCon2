#!/usr/bin/env python3
"""Where would the Model 2 core's crosshair have been for every held aim of a GUNDBG=1 session? (run ON the MiSTer)

Takes each pull's held aim (pub_x / pub_y raw, or OFF), applies what the app does (the range the core is given is the picture's
edges, 166..759 x 18..254 in the last 'tracker edges' log line; the MiSTer scales raw to -127..127 with C integer maths) and what the
core does (u = a + 128; px = u * 496 >> 8, py = u * 384 >> 8; off-screen band: px <= 23 or >= 472, py <= 18 or >= 365), and prints a
character map of 496 x 384 with one mark per pull, plus the min / max reached. A perimeter sweep should draw a rectangle."""
import re
CSV = '/tmp/gundbg_out.csv'
LOG = '/tmp/guncal_apply.log'
for line in open(LOG):
	m = re.search(r'tracker edges x (\d+)\.\.(\d+) y (\d+)\.\.(\d+)', line)
	if m:
		x0, x1, y0, y1 = [int(v) for v in m.groups()]
rows = []
for line in open(CSV).read().splitlines()[1:]:
	f = line.split(',')
	if len(f) >= 12:
		try:
			rows.append([int(v) for v in f[:12]])
		except ValueError:
			pass
pulls = [i for i in range(1, len(rows)) if rows[i][4] == 1 and rows[i - 1][4] == 0]


def stick(v, lo, hi):
	c = (lo + hi) // 2
	h = (hi - lo) // 2
	v = max(lo, min(hi, v)) - c
	a = int(v * 127 / h)                 # C truncation toward zero
	return max(-127, min(127, a))


W, H = 62, 24
grid = [['.'] * W for _ in range(H)]
n_on = n_off = 0
pxs, pys = [], []
for k, i in enumerate(pulls):
	t = rows[i][1]
	nxt = rows[pulls[k + 1]][1] if k + 1 < len(pulls) else 10 ** 12
	after = [r for r in rows[i:] if r[1] <= t + 600 and r[1] < nxt]
	held = after[-1] if after else rows[i]
	if held[11]:
		n_off += 1
		continue
	n_on += 1
	ux = stick(held[9], x0, x1) + 128
	uy = stick(held[10], y0, y1) + 128
	px, py = ux * 496 >> 8, uy * 384 >> 8
	pxs.append(px); pys.append(py)
	off = px <= 23 or px >= 472 or py <= 18 or py >= 365
	gx, gy = min(W - 1, px * W // 496), min(H - 1, py * H // 384)
	grid[gy][gx] = '#' if off else ('o' if grid[gy][gx] in '.o' else '#') if False else ('X' if off else 'o')
print('held on-screen %d, offscreen %d; core crosshair px %d..%d (of 0..495), py %d..%d (of 0..383)' % (n_on, n_off, min(pxs), max(pxs), min(pys), max(pys)))
print('o = on screen, X = the core would call it off-screen; each cell is 8 px wide, 16 high')
print('+' + '-' * W + '+')
for r in grid:
	print('|' + ''.join(r) + '|')
print('+' + '-' * W + '+')

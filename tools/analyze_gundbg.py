#!/usr/bin/env python3
"""Summarise a GunCon 2 trace taken with the GUNDBG build of Main_MiSTer.

  python tools/analyze_gundbg.py captures/gundbg.csv [captures/gundbg_out.csv]

gundbg.csv      raw evdev events as MiSTer read them: kernel_s,read_s,type,code,value
gundbg_out.csv  (optional) what the tracker decided: dev,t_ms,raw_x,raw_y,trig,shot,out_x,out_y,offscreen

Answers the questions that decide the design:
  - how often does the gun report, and how late does MiSTer see each report?
  - which raw X values mean "light" and which mean "none"?
  - after a trigger pull, how long until the game's flash blanks the gun, how long is it blank, and how
    long until it sees the flash? (the lag between the flash and a usable position)
  - what did the tracker do with all that?
"""
import collections
import statistics
import sys

EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
TRIGGER = 0x133            # BTN_X, the GunCon 2 trigger as the kernel driver reports it
X_VALID_MIN = 16           # same default as LIGHTGUN_CRT_X_VALID_MIN


def load_raw(path):
	"""Return [(t_s, x, y, trigger, read_lag_ms)] one entry per SYN_REPORT."""
	rows, x, y, trig = [], 0, 0, 0
	for line in open(path).read().splitlines()[1:]:
		k, r, t, c, v = line.split(',')
		k, r, t, c, v = float(k), float(r), int(t), int(c), int(v)
		if t == EV_ABS and c == 0:
			x = v
		elif t == EV_ABS and c == 1:
			y = v
		elif t == EV_KEY and c == TRIGGER:
			trig = v
		elif t == EV_SYN:
			rows.append((k, x, y, trig, (r - k) * 1000.0))
	return rows


def pct(vals, p):
	vals = sorted(vals)
	return vals[min(len(vals) - 1, int(len(vals) * p))]


def summarise(rows):
	if len(rows) < 3:
		print('too few reports (%d)' % len(rows))
		return
	t0 = rows[0][0]
	dur = rows[-1][0] - t0
	print('reports (changes only): %d over %.1f s' % (len(rows), dur))
	gaps = [(rows[i + 1][0] - rows[i][0]) * 1000 for i in range(len(rows) - 1)]
	print('gap between reports ms: min %.1f  median %.1f  p90 %.1f  p99 %.1f  max %.1f' % (
		min(gaps), statistics.median(gaps), pct(gaps, .9), pct(gaps, .99), max(gaps)))
	lag = [r[4] for r in rows]
	print('MiSTer read lag ms:     median %.2f  p99 %.2f  max %.2f' % (statistics.median(lag), pct(lag, .99), max(lag)))

	valid = [r for r in rows if r[1] >= X_VALID_MIN]
	print('X >= %d (light): %d of %d reports (%.0f%%)' % (X_VALID_MIN, len(valid), len(rows), 100.0 * len(valid) / len(rows)))
	if valid:
		xs, ys = [r[1] for r in valid], [r[2] for r in valid]
		print('valid range: x %d..%d  y %d..%d' % (min(xs), max(xs), min(ys), max(ys)))
	low = collections.Counter(r[1] for r in rows if r[1] < X_VALID_MIN)
	print('X values below the threshold (no light):', dict(low.most_common(6)))
	ys_dark = collections.Counter(r[2] for r in rows if r[1] < X_VALID_MIN)
	print('Y values seen while X says no light:    ', dict(ys_dark.most_common(6)))

	presses = [i for i in range(1, len(rows)) if rows[i][3] and not rows[i - 1][3]]
	print('\ntrigger pulls: %d' % len(presses))
	flashes = 0
	for n, i in enumerate(presses, 1):
		tp = rows[i][0]
		window = [r for r in rows[i:] if r[0] - tp <= 0.6]
		before = [r for r in rows[:i] if r[1] >= X_VALID_MIN]
		pre = before[-1] if before else None
		was_valid = rows[i][1] >= X_VALID_MIN
		dark_at = next((r[0] - tp for r in window if r[1] < X_VALID_MIN), None)
		back_at = None
		if dark_at is not None:
			back_at = next((r[0] - tp for r in window if r[0] - tp > dark_at and r[1] >= X_VALID_MIN), None)
		after = next((r for r in window if dark_at is not None and r[0] - tp > dark_at and r[1] >= X_VALID_MIN), None)
		if dark_at is not None and was_valid:
			flashes += 1
		print('  #%-2d valid at pull: %-3s  first no-light after %s  light again after %s  | before (%s) -> flash (%s)' % (
			n, 'yes' if was_valid else 'NO',
			'%.0f ms' % (dark_at * 1000) if dark_at is not None else 'never',
			'%.0f ms' % (back_at * 1000) if back_at is not None else 'never',
			'%d,%d' % (pre[1], pre[2]) if pre else '-',
			'%d,%d' % (after[1], after[2]) if after else '-'))
	if presses:
		print('pulls followed by a blank-then-flash pattern: %d of %d' % (flashes, len(presses)))


def summarise_out(path):
	rows = []
	for line in open(path).read().splitlines()[1:]:
		dev, t, rx, ry, trig, shot, ox, oy, off = (int(v) for v in line.split(','))
		rows.append((t, rx, ry, trig, shot, ox, oy, off))
	if not rows:
		return
	n = len(rows)
	off = sum(r[7] for r in rows)
	held = sum(1 for r in rows if r[1] < X_VALID_MIN and not r[7])
	print('\ntracker: %d decisions: %d tracking, %d held (dark/flash), %d offscreen; shot windows opened: %d' % (
		n, n - held - off, held, off, sum(1 for i in range(1, n) if rows[i][4] and not rows[i - 1][4])))


if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.exit(__doc__)
	summarise(load_raw(sys.argv[1]))
	if len(sys.argv) > 2:
		summarise_out(sys.argv[2])

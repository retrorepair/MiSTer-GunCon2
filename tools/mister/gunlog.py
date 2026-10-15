#!/usr/bin/env python3
"""Log GunCon 2 reports on the MiSTer HPS (runs on the MiSTer; python3 is present, gcc is not).

Reads the gun's evdev node, records every report the kernel driver publishes, then prints
a summary: report cadence, how often the gun reports (0, 0) = "no light seen", and for every
trigger pull the delay to the first (0, 0) report and to the first valid report after it.

Note: evdev drops reports whose values did not change, so cadence is only meaningful while
the gun is moving or jittering. Keep the gun moving a little for the cadence numbers.

usage: python3 gunlog.py [seconds=30] [csv=/tmp/gunlog.csv]
"""
import os
import select
import struct
import sys
import time

EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
ABS_X, ABS_Y = 0, 1
BTN_TRIGGER = 0x133  # the driver maps the GunCon 2 trigger to BTN_X
EVENT = struct.Struct('llHHi')  # struct input_event on 32-bit ARM Linux; native sizes elsewhere


def find_event_node():
	for block in open('/proc/bus/input/devices').read().split('\n\n'):
		if 'GunCon 2' in block:
			for tok in block.split():
				if tok.startswith('event'):
					return '/dev/input/' + tok
	return None


def wait_for_node(timeout):
	end = time.time() + timeout
	while time.time() < end:
		node = find_event_node()
		if node:
			return node
		time.sleep(0.5)
	return None


def record(path, seconds):
	"""Return [(t_ms, x, y, trigger)], one entry per SYN_REPORT. Stops early if the gun disconnects."""
	rows = []
	x = y = trig = 0
	t0 = None
	fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
	end = time.time() + seconds
	buf = b''
	try:
		while time.time() < end:
			if not select.select([fd], [], [], 0.2)[0]:
				continue
			try:
				chunk = os.read(fd, 4096)
			except OSError:
				print('gun disconnected during capture')
				break
			buf += chunk
			while len(buf) >= EVENT.size:
				sec, usec, etype, code, value = EVENT.unpack(buf[:EVENT.size])
				buf = buf[EVENT.size:]
				t = sec * 1000.0 + usec / 1000.0
				if t0 is None:
					t0 = t
				if etype == EV_ABS and code == ABS_X:
					x = value
				elif etype == EV_ABS and code == ABS_Y:
					y = value
				elif etype == EV_KEY and code == BTN_TRIGGER:
					trig = value
				elif etype == EV_SYN:
					rows.append((t - t0, x, y, trig))
	finally:
		os.close(fd)
	return rows


def pct(sorted_vals, p):
	return sorted_vals[min(len(sorted_vals) - 1, int(len(sorted_vals) * p))]


def analyse(rows, window_ms=600.0):
	out = []
	if len(rows) < 2:
		return ['not enough reports (%d)' % len(rows)]
	dur = (rows[-1][0] - rows[0][0]) / 1000.0
	out.append('reports: %d over %.1f s (%.1f/s, changes only)' % (len(rows), dur, len(rows) / dur if dur else 0))

	gaps = sorted(rows[i + 1][0] - rows[i][0] for i in range(len(rows) - 1))
	out.append('gap ms: min %.1f  median %.1f  p90 %.1f  max %.1f' % (gaps[0], pct(gaps, 0.5), pct(gaps, 0.9), gaps[-1]))

	zero = [r for r in rows if r[1] == 0 and r[2] == 0]
	valid = [r for r in rows if not (r[1] == 0 and r[2] == 0)]
	out.append('(0,0) no-light reports: %d of %d (%.0f%%)' % (len(zero), len(rows), 100.0 * len(zero) / len(rows)))
	if valid:
		xs = [r[1] for r in valid]
		ys = [r[2] for r in valid]
		out.append('valid range: x %d..%d  y %d..%d' % (min(xs), max(xs), min(ys), max(ys)))

	presses = [rows[i][0] for i in range(1, len(rows)) if rows[i][3] and not rows[i - 1][3]]
	out.append('trigger pulls: %d' % len(presses))
	for n, tp in enumerate(presses, 1):
		after = [r for r in rows if tp <= r[0] <= tp + window_ms]
		tz = next((r[0] - tp for r in after if r[1] == 0 and r[2] == 0), None)
		tv = None
		if tz is not None:
			tv = next((r[0] - tp for r in after if r[0] - tp > tz and not (r[1] == 0 and r[2] == 0)), None)
		before = [r for r in rows if r[0] < tp and not (r[1] == 0 and r[2] == 0)]
		last = before[-1] if before else None
		out.append('  #%d: first (0,0) after %s ms, valid again after %s ms, last valid before pull: %s' % (
			n,
			'%.0f' % tz if tz is not None else 'never',
			'%.0f' % tv if tv is not None else 'never',
			'(%d,%d) %.0f ms earlier' % (last[1], last[2], tp - last[0]) if last else 'none'))
	return out


if __name__ == '__main__':
	seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
	csv = sys.argv[2] if len(sys.argv) > 2 else '/tmp/gunlog.csv'
	print('waiting up to 120 s for the GunCon 2 ...')
	node = wait_for_node(120)
	if not node:
		sys.exit('GunCon 2 never appeared')
	print('logging %s for %.0f s ...' % (node, seconds))
	rows = record(node, seconds)
	with open(csv, 'w') as f:
		f.write('t_ms,x,y,trigger\n')
		for r in rows:
			f.write('%.1f,%d,%d,%d\n' % r)
	print('\n'.join(analyse(rows)))
	print('csv: %s' % csv)

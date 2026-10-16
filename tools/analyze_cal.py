#!/usr/bin/env python3
"""What the GunCal calibration actually measured: the saved fit and the raw reports behind each shot.
Runs on the PC or on the MiSTer:   python3 analyze_cal.py /tmp/gundbg.csv /media/fat/config/GUNCAL_uni_0b9a_016a_v1.cfg
"""
import os
import statistics
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_gundbg as a

rows = a.load_raw(sys.argv[1])
if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
	v = struct.unpack('<6i', open(sys.argv[2], 'rb').read(24))
	print('saved fit: raw_x = %.4f*px + %.1f   raw_y = %.4f*py + %.1f' % (v[1] / 1000, v[2] / 1000, v[3] / 1000, v[4] / 1000))

presses = [i for i in range(1, len(rows)) if rows[i][3] and not rows[i - 1][3]]
print('trigger pulls in the trace:', len(presses))
for n, i in enumerate(presses, 1):
	tp = rows[i][0]
	win = [r for r in rows[i:] if r[0] - tp <= 0.3 and r[1] >= a.X_VALID_MIN]
	if len(win) >= 2:
		xs = [r[1] for r in win]
		ys = [r[2] for r in win]
		print('  pull %2d at +%.1fs: %2d valid reports in 300 ms  x %4d..%4d med %4d | y %3d..%3d med %3d | first valid after %3.0f ms' % (
			n, tp - rows[0][0], len(win), min(xs), max(xs), statistics.median(xs), min(ys), max(ys), statistics.median(ys), (win[0][0] - tp) * 1000))
	else:
		print('  pull %2d at +%.1fs: %d valid reports (no light)' % (n, tp - rows[0][0], len(win)))

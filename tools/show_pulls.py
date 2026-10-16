#!/usr/bin/env python3
"""Print the gun's reports around every trigger pull in a GUNDBG trace (runs on the PC or the MiSTer).

  python tools/show_pulls.py captures/gundbg.csv [before_ms=200] [after_ms=400] [max_pulls=12]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_gundbg as a

rows = a.load_raw(sys.argv[1])
before = float(sys.argv[2]) / 1000 if len(sys.argv) > 2 else 0.2
after = float(sys.argv[3]) / 1000 if len(sys.argv) > 3 else 0.4
maxp = int(sys.argv[4]) if len(sys.argv) > 4 else 12
presses = [i for i in range(1, len(rows)) if rows[i][3] and not rows[i - 1][3]]
print('%d reports, %d trigger pulls' % (len(rows), len(presses)))
for n, i in enumerate(presses[:maxp], 1):
	tp = rows[i][0]
	seq = [r for r in rows if -before <= r[0] - tp <= after]
	line = []
	for r in seq:
		dt = int((r[0] - tp) * 1000)
		line.append('%+d:%s' % (dt, ('%d,%d' % (r[1], r[2])) if r[1] >= a.X_VALID_MIN else '-'))
	print('pull %d: %s' % (n, '  '.join(line)))

#!/usr/bin/env python3
"""Write a MiSTer per-core button map for the GunCon 2 (runs on the MiSTer).

This is the file the OSD "Define joystick buttons" wizard saves: 32 little-endian u32, index = the core's
joystick bit (0..3 d-pad, then the core's J1 buttons in order), value = evdev key code.

usage: python3 make_gun_map.py <CoreName> <button index of the trigger target> [A B Select Start indexes...]
  NES: python3 make_gun_map.py NES 10 4 5 6 7     (A=4 B=5 Select=6 Start=7, Zapper/Vaus Btn=10)
The gun's buttons as the kernel driver reports them: trigger BTN_X 0x133, A 0x130, B 0x131, C 0x134,
Start 0x13b, Select 0x13a.
"""
import os
import struct
import sys

core = sys.argv[1]
trigger_idx = int(sys.argv[2])
a, b, sel, start = (int(v) for v in sys.argv[3:7]) if len(sys.argv) >= 7 else (None,) * 4

m = [0] * 32
m[trigger_idx] = 0x133
for idx, code in ((a, 0x130), (b, 0x131), (sel, 0x13a), (start, 0x13b)):
	if idx is not None:
		m[idx] = code

path = '/media/fat/config/inputs/%s_input_0b9a_016a_v3.map' % core
if os.path.exists(path):
	sys.exit('refusing to overwrite %s' % path)
open(path, 'wb').write(struct.pack('<32I', *m))
print('wrote %s' % path)
print([hex(v) for v in m[:12]])

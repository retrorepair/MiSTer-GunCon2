#!/usr/bin/env python3
"""Render the GunCal core's screens in simulation (iverilog) to PNGs, shown the way a 4:3 tube shows them (640 x 480).

usage (from the repo root, inside WSL where iverilog is):  python3 cores/GunCal/tools/render_frames.py <outdir>
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RTL = os.path.join(HERE, '..', 'rtl')
W, H = 529, 480

SCENES = {
	'p1_intro':         dict(page=1, target=0, tx=264, ty=120, intro=1),
	'p1_centre':        dict(page=1, target=0, tx=264, ty=120),
	'p1_top_left':      dict(page=1, target=1, tx=63, ty=28),
	'p1_bottom_right':  dict(page=1, target=3, tx=465, ty=211),
	'p1_missed':        dict(page=1, target=2, tx=465, ty=28, msg=1),         # a refused shot draws nothing extra
	'p1_margin30':      dict(page=1, target=4, tx=159, ty=168),
	'p2_check':         dict(page=2, tx=264, ty=120, pvalid=1, px=270, py=124),
	'p2_hot_exit':      dict(page=2, tx=264, ty=120, pvalid=1, px=380, py=185),
	'p0_monitor':       dict(page=0, pvalid=1, px=264, py=120),
}


def render(name, args, outdir, exe):
	txt = os.path.join(outdir, name + '.txt')
	cmd = ['vvp', exe] + ['+%s=%s' % (k, v) for k, v in args.items()] + ['+out=' + txt]
	subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
	img = Image.new('RGB', (W, H), (0, 0, 0))
	px = img.load()
	for line in open(txt):
		hc, y, rgb = line.split()
		hc, y, rgb = int(hc), int(y), int(rgb, 16)
		if 0 <= hc < W and 0 <= y < H:
			px[hc, y] = ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
	os.remove(txt)
	tv = img.resize((640, 480), Image.NEAREST)           # the 480 rows of both fields, on a 4:3 screen
	# faint markers of where a CRT typically hides picture (about 4% each side): the area a target must stay out of
	d = ImageDraw.Draw(tv)
	d.rectangle([26, 19, 613, 460], outline=(255, 0, 255))
	tv.save(os.path.join(outdir, name + '.png'))


def main():
	outdir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
	os.makedirs(outdir, exist_ok=True)
	exe = os.path.join('/tmp', 'guncal_tb')
	subprocess.run(['iverilog', '-g2012', '-o', exe, os.path.join(RTL, 'guncal.v'), os.path.join(RTL, 'guncal_text.v'),
	                os.path.join(RTL, 'font5x7.v'), os.path.join(HERE, 'tb_frame.v')], check=True)
	for name, args in SCENES.items():
		render(name, args, outdir, exe)
		print('rendered', name)


if __name__ == '__main__':
	main()

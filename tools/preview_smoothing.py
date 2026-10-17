#!/usr/bin/env python3
"""Preview of the Filled mode's vertical smoothing from a real screenshot of the plain 4:5 build (stdlib only).

The screenshot is the 480-row frame B(m) the converter's plain blend produces. The smoothing is out(m) = B(m-1)/4 + B(m)/2 + B(m+1)/4
(rows clamped), exactly what the hardware does on top of B, so the 'after' image is the real result for that picture. Each panel shows
what one field puts on the tube (its rows, the other field's rows dark) and then the two together.

  python tools/preview_smoothing.py captures/shots/vcop_filled_b.png captures/shots/preview_smoothing.png
"""
import struct
import sys
import zlib


def read_rgb(path):
	d = open(path, 'rb').read()
	pos, idat, hdr = 8, b'', None
	while pos < len(d):
		ln, typ = struct.unpack('>I4s', d[pos:pos + 8])
		body = d[pos + 8:pos + 8 + ln]
		if typ == b'IHDR': hdr = struct.unpack('>IIBBBBB', body)
		elif typ == b'IDAT': idat += body
		pos += 12 + ln
	w, h, depth, ctype, _, _, il = hdr
	assert depth == 8 and il == 0 and ctype in (2, 6), hdr
	bpp = 3 if ctype == 2 else 4
	raw = zlib.decompress(idat)
	stride = w * bpp
	rows, prev = [], bytearray(stride)
	for y in range(h):
		f = raw[y * (stride + 1)]
		line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
		for i in range(stride):
			a = line[i - bpp] if i >= bpp else 0
			b = prev[i]
			c = prev[i - bpp] if i >= bpp else 0
			if f == 1: line[i] = (line[i] + a) & 255
			elif f == 2: line[i] = (line[i] + b) & 255
			elif f == 3: line[i] = (line[i] + ((a + b) >> 1)) & 255
			elif f == 4:
				p = a + b - c
				pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
				pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
				line[i] = (line[i] + pr) & 255
		rows.append(bytes(line[i] for i in range(stride) if bpp == 3 or i % 4 != 3))
		prev = line
	return w, h, rows   # rows of w*3 bytes


def write_png(path, w, h, rows):
	def chunk(t, b): return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xFFFFFFFF)
	raw = b''.join(b'\x00' + r for r in rows)
	open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
	                       chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def smooth(rows):
	n = len(rows)
	out = []
	for m in range(n):
		a, b, c = rows[max(m - 1, 0)], rows[m], rows[min(m + 1, n - 1)]
		out.append(bytes((x + 2 * y + z + 2) >> 2 for x, y, z in zip(a, b, c)))
	return out


def field(rows, parity):
	dark = bytes(len(rows[0]))
	return [r if (m & 1) == parity else dark for m, r in enumerate(rows)]


def crop(rows, x0, x1, y0, y1):
	return [r[x0 * 3:x1 * 3] for r in rows[y0:y1]]


def zoom(rows, k):
	out = []
	for r in rows:
		z = b''.join(r[i:i + 3] * k for i in range(0, len(r), 3))
		out.extend([z] * k)
	return out


def beside(panels, gap=8):
	h = max(len(p) for p in panels)
	rows = []
	for y in range(h):
		parts = []
		for p in panels:
			parts.append(p[y] if y < len(p) else bytes(len(p[0])))
			parts.append(bytes([40, 40, 40]) * gap)
		rows.append(b''.join(parts[:-1]))
	return rows


def stack(blocks, gap=10):
	w = max(len(b[0]) for b in blocks)
	rows = []
	for b in blocks:
		rows.extend(r + bytes([40, 40, 40]) * ((w - len(r)) // 3) for r in b)
		rows.extend([bytes([40, 40, 40]) * (w // 3)] * gap)
	return rows[:-gap]


def interline(rows):
	"""mean |row m - row m+1| over the frame: what a viewer sees flicker as, between the two fields."""
	t = n = 0
	for a, b in zip(rows, rows[1:]):
		t += sum(abs(x - y) for x, y in zip(a, b))
		n += len(a)
	return t / n


def main():
	src, dst = sys.argv[1], sys.argv[2]
	w, h, rows = read_rgb(src)
	sm = smooth(rows)
	print('interline difference (mean |row - next row|, 0..255): sharp %.2f, smoothed %.2f (%.0f%% of it left)' %
	      (interline(rows), interline(sm), 100 * interline(sm) / interline(rows)))
	k = 4
	blocks = []
	for (x0, x1, y0, y1) in ((104, 200, 178, 226), (205, 291, 436, 462)):
		for img in (rows, sm):
			c = crop(img, x0, x1, y0, y1)
			blocks.append(beside([zoom(field(c, 0), k), zoom(field(c, 1), k), zoom(c, k)]))
	out = stack(blocks)
	write_png(dst, len(out[0]) // 3, len(out), out)
	print('wrote', dst, len(out[0]) // 3, 'x', len(out))


main()

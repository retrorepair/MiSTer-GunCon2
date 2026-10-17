#!/usr/bin/env python3
"""Minimal PNG reader (8-bit, non-interlaced, gray/RGB/RGBA/palette-less) returning rows of grey values; no third-party packages."""
import struct
import zlib


def read_png(path):
	d = open(path, 'rb').read()
	assert d[:8] == b'\x89PNG\r\n\x1a\n'
	pos, idat, hdr = 8, b'', None
	while pos < len(d):
		ln, typ = struct.unpack('>I4s', d[pos:pos + 8])
		body = d[pos + 8:pos + 8 + ln]
		if typ == b'IHDR': hdr = struct.unpack('>IIBBBBB', body)
		elif typ == b'IDAT': idat += body
		pos += 12 + ln
	w, h, depth, ctype, _, _, interlace = hdr
	assert depth == 8 and interlace == 0 and ctype in (0, 2, 6), hdr
	bpp = {0: 1, 2: 3, 6: 4}[ctype]
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
				pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
				line[i] = (line[i] + pr) & 255
		rows.append(line)
		prev = line
	grey = []
	for r in rows:
		if bpp == 1: grey.append(list(r))
		else: grey.append([(r[i] + r[i + 1] + r[i + 2]) // 3 for i in range(0, stride, bpp)])
	return w, h, grey

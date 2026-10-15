#!/usr/bin/env python3
"""Read raw GunCon 2 USB reports on the MiSTer through usbfs (runs on the MiSTer).

Unlike evdev this sees every 6-byte report (evdev drops unchanged values) and the bytes
the kernel driver ignores. It needs the interface, so the guncon2 kernel driver is unbound
for the duration and rebound afterwards (MiSTer sees the gun disappear and come back).

usage: python3 usbraw.py [seconds=20] [out=/tmp/usbraw.log]
"""
import array
import collections
import fcntl
import os
import select
import struct
import sys
import time

IFACE = '1-1.2:1.0'         # located below by vid:pid; this is only the fallback
VID, PID = '0b9a', '016a'
EP = 0x81

def _ioc(d, nr, size):
	return (d << 30) | (size << 16) | (0x55 << 8) | nr
URB = struct.Struct('<BBxxiIIiiiIiII')
assert URB.size == 44
SUBMITURB = _ioc(2, 10, URB.size)
REAPURBNDELAY = _ioc(1, 13, 4)
CLAIMINTERFACE = _ioc(2, 15, 4)
CONTROL = _ioc(3, 0, 16)


def addr(a):
	return a.buffer_info()[0]


def arg(a):
	# fcntl.ioctl takes a signed C long; user addresses above 2 GiB must be passed as negatives
	v = addr(a)
	return v - (1 << 32) if v >= 1 << 31 else v


def find_device():
	base = '/sys/bus/usb/devices/'
	for d in os.listdir(base):
		p = base + d
		try:
			if open(p + '/idVendor').read().strip() == VID and open(p + '/idProduct').read().strip() == PID:
				return d, int(open(p + '/busnum').read()), int(open(p + '/devnum').read())
		except OSError:
			pass
	sys.exit('GunCon 2 not found')


def main(seconds, out):
	dev, bus, num = find_device()
	iface = dev + ':1.0'
	node = '/dev/bus/usb/%03d/%03d' % (bus, num)
	driver = '/sys/bus/usb/drivers/guncon2/'
	print('device %s at %s, unbinding driver' % (dev, node))
	open(driver + 'unbind', 'w').write(iface)
	rows = []
	try:
		fd = os.open(node, os.O_RDWR)
		num_if = array.array('I', [0])
		fcntl.ioctl(fd, CLAIMINTERFACE, arg(num_if))

		# same mode request the kernel driver sends on open: byte 5 = 1
		cdata = array.array('B', [0, 0, 0, 0, 0, 1])
		ctl = array.array('B', struct.pack('<BBHHHII', 0x21, 0x09, 0x200, 0, 6, 500, addr(cdata)))
		try:
			fcntl.ioctl(fd, CONTROL, arg(ctl))
			print('mode request sent')
		except OSError as e:
			print('mode request failed: %s' % e)

		buf = array.array('B', [0] * 8)
		urb = array.array('B', [0] * URB.size)
		reaped = array.array('I', [0])

		def submit():
			urb[:] = array.array('B', URB.pack(1, EP, 0, 0, addr(buf), 8, 0, 0, 0, 0, 0, 0))
			fcntl.ioctl(fd, SUBMITURB, arg(urb))

		poll = select.poll()
		poll.register(fd, select.POLLOUT)
		submit()
		t0 = time.time()
		while time.time() - t0 < seconds:
			if not poll.poll(200):
				continue
			try:
				fcntl.ioctl(fd, REAPURBNDELAY, arg(reaped))
			except OSError:
				continue
			t = time.time() - t0
			status, actual = struct.unpack_from('<i', urb, 4)[0], struct.unpack_from('<i', urb, 20)[0]
			rows.append((t, status, bytes(buf[:max(actual, 0)])))
			submit()
		os.close(fd)
	finally:
		open(driver + 'bind', 'w').write(iface)
		print('driver rebound')

	with open(out, 'w') as f:
		for t, st, b in rows:
			f.write('%.4f %d %s\n' % (t, st, b.hex()))
	print('reports: %d in %d s (log: %s)' % (len(rows), seconds, out))
	if not rows:
		return
	gaps = sorted((rows[i + 1][0] - rows[i][0]) * 1000 for i in range(len(rows) - 1))
	if gaps:
		print('gap ms: min %.1f median %.1f p90 %.1f max %.1f' % (gaps[0], gaps[len(gaps) // 2], gaps[int(len(gaps) * .9)], gaps[-1]))
	print('status counts:', dict(collections.Counter(st for _, st, _ in rows)))
	print('lengths:', dict(collections.Counter(len(b) for _, _, b in rows)))
	for i in range(6):
		vals = collections.Counter(b[i] for _, _, b in rows if len(b) > i)
		print('byte%d distinct: %s' % (i, dict(vals.most_common(8))))
	print('top payloads:', collections.Counter(b.hex() for _, _, b in rows).most_common(8))


if __name__ == '__main__':
	main(float(sys.argv[1]) if len(sys.argv) > 1 else 20.0, sys.argv[2] if len(sys.argv) > 2 else '/tmp/usbraw.log')

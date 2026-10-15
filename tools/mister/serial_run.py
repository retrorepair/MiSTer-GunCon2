#!/usr/bin/env python3
"""Run commands / push files to the MiSTer over its UART console (COM3 by default).

The MiSTer must already be logged in on the console (log in yourself with console.ps1,
then quit it with Ctrl+]; the shell stays logged in). This never types credentials.

usage:
  serial_run.py run  "<shell command>" [timeout_s]
  serial_run.py push <local file> <remote path>      (small files)
  serial_run.py pushz <local file> <remote path>     (large files; gzip + base64, md5 checked)
  serial_run.py pull <remote path> <local file>
"""
import base64
import sys
import time

import serial

PORT, BAUD = 'COM3', 115200
SENTINEL = '__DO""NE__'      # typed form; the echo of the typed line differs from the real output
SENTINEL_OUT = '__DONE__'


class Mister:
	def __init__(self, port=PORT, baud=BAUD):
		self.s = serial.Serial(port, baud, timeout=0.2)
		self.s.reset_input_buffer()
		self.s.write(b'\r')
		time.sleep(0.5)
		greeting = self.s.read(4096).decode('utf-8', 'replace')
		if 'login:' in greeting.split('\n')[-1] or greeting.rstrip().endswith('Password:'):
			raise SystemExit('MiSTer console is at a login prompt - log in first (tools/mister/console.ps1).')

	def run(self, cmd, timeout=15.0):
		self.s.reset_input_buffer()
		self.s.write((cmd + '; echo ' + SENTINEL + '\r').encode())
		buf = ''
		end = time.time() + timeout
		while time.time() < end:
			buf += self.s.read(4096).decode('utf-8', 'replace')
			if SENTINEL_OUT in buf.replace('\r', ''):
				break
		else:
			raise TimeoutError('no completion marker; output so far:\n' + buf)
		text = buf.replace('\r', '')
		# drop the echoed command line and the marker line
		lines = text.split('\n')
		body = [l for l in lines[1:] if SENTINEL_OUT not in l]
		return '\n'.join(body).strip()

	def push(self, local, remote, chunk=400):
		data = base64.b64encode(open(local, 'rb').read()).decode()
		tmp = remote + '.b64'
		self.run('rm -f %s' % tmp)
		for i in range(0, len(data), chunk):
			self.run("echo '%s' >> %s" % (data[i:i + chunk], tmp))
		self.run('python3 -c "import base64;open(\'%s\',\'wb\').write(base64.b64decode(open(\'%s\').read()))"' % (remote, tmp))
		self.run('rm -f %s' % tmp)
		return self.run('wc -c %s' % remote)


def pull(m, remote, local):
	"""Fetch a file: gzip + base64 printed by the MiSTer, decoded here, md5-verified."""
	import gzip
	import hashlib
	import re
	# work on a snapshot: live log files keep growing while we read them
	m.run('cp %s /tmp/pull.src && gzip -c /tmp/pull.src > /tmp/pull.gz; md5sum /tmp/pull.src | cut -d" " -f1 > /tmp/pull.md5; rm -f /tmp/pull.src' % remote, 60)
	want = m.run('cat /tmp/pull.md5').split()[0]
	py = "python3 -c \"import base64;print(base64.b64encode(open('/tmp/pull.gz','rb').read()).decode())\""
	for attempt in range(4):          # the UART occasionally drops a character; the md5 catches it, so just retry
		try:
			text = m.run('base64 /tmp/pull.gz 2>/dev/null || ' + py, 300)
			data = gzip.decompress(base64.b64decode(re.sub(r'\s+', '', text)))
			if hashlib.md5(data).hexdigest() == want:
				break
		except Exception:
			pass
		m.s.reset_input_buffer()
	else:
		raise SystemExit('pull corrupted after 4 attempts')
	open(local, 'wb').write(data)
	m.run('rm -f /tmp/pull.gz /tmp/pull.md5')
	return 'ok %s -> %s (%d bytes)' % (remote, local, len(data))


def pushz(m, local, remote):
	"""Bulk transfer: gzip + base64 streamed into `cat` in one go, md5-verified on both ends."""
	import gzip
	import hashlib
	raw = open(local, 'rb').read()
	text = base64.encodebytes(gzip.compress(raw, 9))
	want_text = hashlib.md5(text).hexdigest()
	want_bin = hashlib.md5(raw).hexdigest()
	tmp = remote + '.b64'
	m.run('rm -f %s' % tmp)
	m.s.write(('stty -echo; cat > %s\r' % tmp).encode())
	time.sleep(0.5)
	t0 = time.time()
	for i in range(0, len(text), 2048):
		m.s.write(text[i:i + 2048])
	m.s.flush()
	m.s.write(b'\x04')           # EOF; the stream ends with a newline so this is at line start
	time.sleep(1.0)
	m.s.write(b'stty echo\r')
	time.sleep(0.5)
	m.s.reset_input_buffer()
	got = m.run('md5sum %s' % tmp).split()[0]
	if got != want_text:
		raise SystemExit('transfer corrupted: %s != %s' % (got, want_text))
	m.run('python3 -c "import base64,gzip;open(\'%s\',\'wb\').write(gzip.decompress(base64.b64decode(open(\'%s\').read())))"' % (remote, tmp), 60)
	m.run('rm -f %s; chmod +x %s' % (tmp, remote))
	out = m.run('md5sum %s' % remote).split()[0]
	if out != want_bin:
		raise SystemExit('decoded file differs: %s != %s' % (out, want_bin))
	return 'ok %s (%d bytes, %.0f s)' % (remote, len(raw), time.time() - t0)


if __name__ == '__main__':
	m = Mister()
	if sys.argv[1] == 'run':
		print(m.run(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 15.0))
	elif sys.argv[1] == 'pull':
		print(pull(m, sys.argv[2], sys.argv[3]))
	elif sys.argv[1] == 'pushz':
		print(pushz(m, sys.argv[2], sys.argv[3]))
	elif sys.argv[1] == 'push':
		print(m.push(sys.argv[2], sys.argv[3]))
	else:
		raise SystemExit(__doc__)

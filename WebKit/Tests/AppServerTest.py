import unittest
import os
import fcntl
import time
import signal
import re

class AppServerTest(unittest.TestCase):

	def setUp(self):
		# start the appserver
		workdir = self.workDir()
		dirname = os.path.dirname
		webwaredir = dirname(dirname(dirname(workdir)))
		launch = os.path.join(workdir, 'Launch.py')
		cmd = "python %s --webware-dir=%s --work-dir=%s" \
			" ThreadedAppServer http" % (launch, webwaredir, workdir)
		# print cmd
		dummy, self._output = os.popen4(cmd)
		# set the output from the appserver to non-blocking mode, so that
		# we can test the output without waiting indefinitely. This is
		# Posix-specific, but there is probably a Win32 equivalent.
		fcntl.fcntl(self._output.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
		self.assertAppServerSays('^Ready (.*).$', wait=10)

	def assertAppServerSays(self, pattern, flags=re.MULTILINE, wait=5):
		"""Check that the appserver output contains the specified pattern.

		If the appserver does not output the pattern within the given number
		of seconds, an assertion is raised.

		"""
		if not self.waitForAppServer(pattern, flags, wait):
			assert False, "Expected appserver to say '%s'," \
				" but after waiting %d seconds it said: %s" \
				% (pattern, wait, self._actualAppServerOutput)

	def waitForAppServer(self, pattern, flags=re.MULTILINE, wait=5):
		"""Check that the appserver output contains the specified pattern.

		Returns True or False depending on whether the pattern was seen.

		"""
		start = time.time()
		data = ''
		while 1:
			data += self.getOutput()
			if re.search(pattern, data, flags):
				return True
			time.sleep(0.2)
			now = time.time()
			if now - start > wait:
				break
		self._actualAppServerOutput = data
		return False

	def getOutput(self):
		data = ''
		try:
			data = self._output.read()
		except IOError, e:
			pass
		return data

	def tearDown(self):
		try:
			pidfile = open(os.path.join(self.workDir(), 'appserverpid.txt'))
		except:
			pass
		else:
			pid = int(pidfile.read())
			pidfile.close()
			os.kill(pid, signal.SIGTERM)
		self.assertAppServerSays('^AppServer has been shutdown.$', wait=10)

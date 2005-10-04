import unittest
import os
import time
from re import compile as reCompile
from threading import Thread
from Queue import Queue, Empty
#~ try:
	#~ import fcntl
#~ except ImportError:
	#~ raise ImportError, 'We currently neeed the fcntl module here,' \
		#~ ' which is unfortunately only available under Unix.'


class AppServerTest(unittest.TestCase):

	def setUp(self):
		# start the appserver
		workdir = self.workDir()
		dirname = os.path.dirname
		webwaredir = dirname(dirname(dirname(workdir)))
		launch = os.path.join(workdir, 'Launch.py')
		self._cmd = "python %s --webware-dir=%s --work-dir=%s" \
			" ThreadedAppServer " % (launch, webwaredir, workdir)
		self._output = os.popen(self._cmd + "start")
		# Set the output from the appserver to non-blocking mode, so that
		# we can test the output without waiting indefinitely. This is
		# Posix-specific, but there is probably a Win32 equivalent.
		# @@ cz: There should be a better solution that works under Win.
		#~ fcntl.fcntl(self._output.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
		def pullStream(stream, queue):
			"""Copy output from stream to queue."""
			while self._output:
				line = self._output.readline()
				if not line:
					break
				self._queue.put(line)
		self._queue = Queue()
		self._thread = Thread(target=pullStream,
			args=(self._output, self._queue))
		self._thread.start()
		self.assertAppServerSays('^Ready (.*).$')

	def assertAppServerSays(self, pattern, wait=5):
		"""Check that the appserver output contains the specified pattern.

		If the appserver does not output the pattern within the given number
		of seconds, an assertion is raised.

		"""
		if not self.waitForAppServer(pattern, wait):
			assert False, "Expected appserver to say '%s',\n" \
				"but after waiting %d seconds it said:\n%s" \
				% (pattern, wait, self._actualAppServerOutput)

	def waitForAppServer(self, pattern, wait=5):
		"""Check that the appserver output contains the specified pattern.

		Returns True or False depending on whether the pattern was seen.

		"""
		start = time.time()
		comp = reCompile(pattern)
		lines = []
		found = False
		while 1:
			try:
				line = self._queue.get_nowait()
				print line
			except Empty:
				line = None
			if line is None:
				now = time.time()
				if now - start > wait:
					break
				time.sleep(0.2)
			else:
				if len(lines) > 9:
					del lines[0]
				lines.append(line)
				if comp.search(line):
					found = True
					break
		self._actualAppServerOutput = ''.join(lines)
		return found

	def tearDown(self):
		print self._cmd + "stop"
		output = os.popen(self._cmd + "stop")
		#print output.read()
		self.assertAppServerSays('^AppServer has been shutdown.$')
		self._output = None

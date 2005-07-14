#!/usr/bin/env python
"""
DebugAppServer executes all requests within the main thread, allowing
servlets to be easily debugged using any Python debugger.  The drawback is
that only one request can be processed at a time using this approach.

Currently the session sweeper is still run within a separate thread, and
a "close thread" is started up by the AppServer base class, but neither
of these two extra threads should pose any problems debugging servlets.

To use, simply run "python Launch.py DebugAppServer" using whatever debugging
environment you prefer.  On Windows, I have tested using both PythonWin
and JEdit with the JPyDbg plugin.
"""

import ThreadedAppServer
import sys, traceback

# We are going to replace ThreadedAppServer with our own class,
# so we need to save a reference to the original class.
OriginalThreadedAppServer = ThreadedAppServer.ThreadedAppServer

class DebugAppServer(OriginalThreadedAppServer):
	"""
	We are piggybacking on 99% of the code in ThreadedAppServer.  Our
	trick is to replace the request queue with a dummy object
	that executes requests immediately instead of pushing them onto
	a queue to be handled by other threads.
	"""
	def __init__(self, path=None):
		# Initialize the base class
		OriginalThreadedAppServer.__init__(self, path)

		# Replace the request queue with a dummy object that merely
		# runs request handlers as soon as they are "pushed"
		self._requestQueue = DummyRequestQueue()

	def config(self):
		# Force ThreadedAppServer to create an empty thread pool by hacking
		# the settings to zero.  This is not strictly necessary to do.
		if self._config is None:
			OriginalThreadedAppServer.config(self)
			self.setSetting('StartServerThreads', 0)
			self.setSetting('MaxServerThreads', 0)
			self.setSetting('MinServerThreads', 0)
		return self._config

	def mainloop(self):
		"""
		This is needed for COM support on Windows, because special
		thread initialization is required on any thread that runs
		servlets, in this case the main thread itself.
		"""
		self.initThread()
		OriginalThreadedAppServer.mainloop(self)
		self.delThread()

class DummyRequestQueue:
	"""
	This is a dummy replacement for the request queue.  It merely
	executes handlers as soon as they are "pushed".
	"""
	def put(self, handler):
		try:
			handler.handleRequest()
		except:
			traceback.print_exc(file=sys.stderr)
		handler.close()


# Replace ThreadedAppServer class in the ThreadedAppServer module with our
# DebugAppServer.  This seems like an awful hack, but it works and
# requires less code duplication than other approaches I could think of, and
# required a very minimal amount of modification to ThreadedAppServer.py.
ThreadedAppServer.ThreadedAppServer = DebugAppServer

# Grab the main function from ThreadedAppServer -- it has been "tricked"
# into using DebugAppServer instead.
main = ThreadedAppServer.main

# Replace Tweak ThreadedAppServer so that it never runs the main loop in a thread
def runMainLoopInThread():
	return 0
ThreadedAppServer.runMainLoopInThread = runMainLoopInThread


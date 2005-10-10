
"""
This module defines `AutoReloadingAppServer`, a replacement for `AppServer`
that adds a file-monitoring and restarting to the AppServer.  It's used
mostly like::

    from AutoReloadingAppServer import AutoReloadingAppServer as AppServer

Much of the actually polling and monitoring takes place in the
`WebKit.ImportSpy` module.

"""

from AppServer import AppServer
import os
from threading import Thread
import time
import sys
import select

try: # backward compatibility for Python < 2.3
	True, False
except NameError:
	True, False = 1, 0

# Attempt to use python-fam (fam = File Alteration Monitor) instead of polling
# to see if files have changed.  If python-fam is not installed, we fall back
# to polling.
try:
	import _fam
	haveFam = True
except:
	haveFam = False

import ImportSpy
standardLibraryPrefix = '%s/lib/python%i.%i' % \
			(sys.prefix, sys.version_info[0], sys.version_info[1])


DefaultConfig = {
	'AutoReload': False,
	'AutoReloadPollInterval': 1, # in seconds
}


class AutoReloadingAppServer(AppServer):
	"""AppServer AutoReloading.

	This class adds functionality to `AppServer`, to notice changes to
	source files, including servlets, PSPs, templates or changes to the
	Webware source file themselves, and reload the server as necessary
	to pick up the changes.

	The server will also be restarted if a file which Webware *tried*
	to import is modified.  This is so that changes to a file containing
	a syntax error (which would have prevented it from being imported)
	will also cause the server to restart.

	"""


	## Init ##

	def __init__(self,path=None):
		"""Activate AutoReloading."""
		AppServer.__init__(self,path)
		self._autoReload = False
		self._shouldRestart = False
		self._requests = []
		self._pipe = None

		if self.isPersistent():
			if self.setting('AutoReload'):
				self.activateAutoReload()

	def defaultConfig(self):
		"""Return the default configuration."""
		conf = AppServer.defaultConfig(self)
		conf.update(DefaultConfig)
		return conf

	def shutDown(self):
		"""Shut down the monitoring thread.

		This is done in addition to the normal shutdown procedure.

		"""
		print 'Stopping AutoReload Monitor...'
		sys.stdout.flush()
		self.running = 1
		self.deactivateAutoReload()
		AppServer.shutDown(self)
		sys.stdout.flush()
		sys.stderr.flush()
		self.running = 0


	## Activatation of AutoReload ##

	def activateAutoReload(self):
		"""Start the monitor thread.W"""
		ImportSpy.modloader.activate()
		if not self._autoReload:
			if haveFam:
				print 'AutoReload Monitor started, using FAM.'
				self._fileMonitorThread = t = Thread(
					target=self.fileMonitorThreadLoopFAM)
			else:
				print 'AutoReload Monitor started, polling every', \
					self.setting('AutoReloadPollInterval'), 'seconds.'
				self._fileMonitorThread = t = Thread(
					target=self.fileMonitorThreadLoop)
			self._autoReload = True
			t.setName('AutoReloadMonitor')
			t.start()

	def deactivateAutoReload(self):
		"""Tell the monitor thread to stop.

		This should be considered as a request, not a demand.

		"""
		self._autoReload = False
		if haveFam:
			# Send a message down the pipe to wake up the monitor thread
			# and tell him to quit.
			self._pipe[1].write('close')
			self._pipe[1].flush()
		try:
			self._fileMonitorThread.join()
		except:
			pass


	## Restart methods ##

	def restartIfNecessary(self):
		"""Check if the app server should be restarted.

		This should be called regularly to see if a restart is required.
		The server can only restart from the main thread, other threads
		can't do the restart. So this polls to see if `shouldRestart`
		has been called.

		"""
		# Tavis Rudd claims: "this method can only be called by
		# the main thread.  If a worker thread calls it, the
		# process will freeze up."
		#
		# I've implemented it so that the ThreadedAppServer's
		# control thread calls this. That thread is _not_ the
		# MainThread (the initial thread created by the Python
		# interpreter), but I've never encountered any problems.
		# Most likely Tavis meant a freeze would occur if a
		# _worker_ called this.
		if self._shouldRestart:
			self.restart()

	def restart(self):
		"""Do the actual restart.

		Call `shouldRestart` from outside the class.

		"""
		sys.stdout.flush()
		sys.stderr.flush()
		# calling execve() is problematic, since the file
		# descriptors don't get closed by the OS.  This can
		# result in leaked database connections.  Instead, we
		# exit with a special return code which is recognized
		# by the AppServer script, which will restart us upon
		# receiving that code.
		sys.exit(3)

	def monitorNewModule(self, filepath, mtime):
		"""Add new file to be monitored.

		This is a callback which ImportSpy invokes to notify us of new files
		to monitor. This is only used when we are using FAM.

		"""
		self._requests.append(self._fc.monitorFile(filepath, filepath) )


	## Internal methods ##

	def shouldRestart(self):
		"""Tell the main thread to restart the server."""
		self._shouldRestart = True

	def fileMonitorThreadLoop(self):
		"""This the the main loop for the monitoring thread.

		Runs in its own thread, polling the files for changes directly
		(i.e., going through every file that's being used and checking
		its last-modified time, seeing if it's been changed since it
		was initially loaded).

		"""
		pollInterval = self.setting('AutoReloadPollInterval')
		while self._autoReload:
			time.sleep(pollInterval)
			for f, mtime in ImportSpy.modloader.fileList().items():
				if self.fileUpdated(f, mtime):
					print '*** The file', f, 'has changed.'
					print
					print 'The AppServer is restarting now...'
					self._autoReload = False
					return self.shouldRestart()
		print 'Autoreload Monitor stopped.'
		sys.stdout.flush()

	def fileUpdated(self, filename, mtime, getmtime=os.path.getmtime):
		"""Check whether a file has been updated.

		Checks if a file has been updated in such a way that we should
		restart the server.

		"""
		try:
			if mtime < getmtime(filename):
				for name, mod in sys.modules.items():
					if getattr(mod, '__file__', None) == filename:
						break
				else:
					# It's not a module, we must reload
					return True
				if getattr(mod, '__donotreload__', None):
					ImportSpy.modloader.fileList()[filename] = getmtime(filename)
					return False
				return True
			else:
				return False
		except OSError:
			return True

	def fileMonitorThreadLoopFAM(self, getmtime=os.path.getmtime):
		"""Monitoring thread loop, but using the FAM library."""
		ImportSpy.modloader.notifyOfNewFiles(self.monitorNewModule)
		self._fc = fc = _fam.open()

		# For all of the modules which have _already_ been loaded, we check
		# to see if they've already been modified or deleted:
		for f, mtime in ImportSpy.modloader.fileList().items():
			if self.fileUpdated(f, mtime):
				print '*** The file', f, 'has changed.', \
					'The server is restarting now.'
				self._autoReload = False
				return self.shouldRestart()
			# request that this file be monitored for changes
			self._requests.append( fc.monitorFile(f, f) )

		# Create a pipe so that this thread can be notified when the
		# server is shutdown. We use a pipe because it needs to be an object
		# which will wake up the call to 'select':
		r,w = os.pipe()
		r = os.fdopen(r, 'r')
		w = os.fdopen(w, 'w')
		self._pipe = pipe = (r, w)
		while self._autoReload:
			try:
				# We block here until a file has been changed, or until
				# we receive word that we should shutdown (via the pipe).
				ri, ro, re = select.select([fc,pipe[0]], [], [])
			except select.error, er:
				errnumber, strerr = er
				if errnumber == errno.EINTR:
					continue
				else:
					print strerr
					sys.exit(1)
			while fc.pending():
				fe = fc.nextEvent()
				if (fe.code2str() in ['changed','deleted','created']
						and self.fileUpdated(fe.userData,
							ImportSpy.modloader.fileList()[fe.userData])):
					print '*** The file', fe.userData, 'has changed.', \
						'The server is restarting now.'
					self._autoReload = False
					return self.shouldRestart()
		for req in self._requests:
			req.cancelMonitor()
		fc.close()
		print 'Autoreload Monitor stopped'
		sys.stdout.flush()

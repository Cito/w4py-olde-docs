import os
import sys
import atexit

def removePidFile(pidfile):
	pidfile.remove()

class PidFile:
	def __init__(self, path):
		self._path = path

		pidfile = open(path, "w")
		if os.name == 'posix':
			pidfile.write(str(os.getpid()))
		else:
			try:
				import win32api
			except:
				print "win32 extensions not present.  Webkit Will not be able to detatch from the controlling terminal."
			if sys.modules.has_key('win32api'):
				pidfile.write(str(win32api.GetCurrentProcess()))

		# delete the pid file when python exits
		atexit.register(removePidFile, self)

	def __del__(self):
		self.remove()

	def remove(self):
		try:
			os.unlink(self._path)
		except OSError:
			pass

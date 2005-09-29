#!/usr/bin/env python

"""AppServerService.py

For general notes, see `ThreadedAppServer`.

This version of the app server is a threaded app server that runs as
a Windows NT Service.  This means it can be started and stopped from
the Control Panel or from the command line using ``net start`` and
``net stop``, and it can be configured in the Control Panel to
auto-start when the machine boots.

This requires the win32all__ package to have been installed.

__ http://www.python.org/windows/win32all/

To see the options for installing, removing, starting, and stopping
the service, just run this program with no arguments.  Typical usage is
to install the service to run under a particular user account and startup
automatically on reboot with::

    python AppServerService.py --username mydomain\myusername \
        --password mypassword --startup auto install

Then, you can start the service from the Services applet in the Control Panel,
where it will be listed as "WebKit Threaded Application Server".  Or, from
the command line, it can be started with either of the following commands::

    net start WebKit
    python AppServerService.py start

The service can be stopped from the Control Panel or with::

    net stop WebKit
    python AppServerService.py stop

And finally, to uninstall the service, stop it and then run::

    python AppServerService.py remove

Currently only one AppServer per system can be set up this way.
"""

# FUTURE
# * This shares a lot of code with ThreadedAppServer.py and Launch.py.
#   Try to consolidate these things. The default settings below in the
#   global variables could go completely into AppServer.config.
# * Optional NT event log messages on start, stop, and errors.
# * Allow the option of installing multiple copies of WebKit with different
#   configurations and different service names.
# * Allow it to work with wkMonitor, or some other fault tolerance mechanism.
# CREDITS
# * Contributed to Webware for Python by Geoff Talvola
# * Changes by Christoph Zwerschke


# You can change the following default values:

# The path to the app server working directory, if you do not
# want to use the directory containing this script:
workDir = None

# The path to the Webware root directory; by default this will
# be the parent directory of the directory containing this script:
webwareDir = None

# A list of additional directories (usually some libraries)
# that you want to include into the search path for modules:
libraryDirs = []

# To get profiling going, set runProfile = 1 (see also
# the description in the docstring of Profiler.py):
runProfile = 0

# The path to the log file, if you want to redirect the
# standard output and standard error to a log file:
logFile = None

# The default app server to be used:
appServer = 'ThreadedAppServer'

# Set debug = 1 if you want to see debugging output:
debug = 0


import win32serviceutil
import win32service
import os, sys, time

# The ThreadedAppServer calls signal.signal which is not possible
# if it is installed as a service, since signal only works in main thread.
# So we sneakily replace signal.signal with a no-op:
def _dummy_signal(*args, **kwargs):
	pass
import signal
signal.signal = _dummy_signal


class AppServerService(win32serviceutil.ServiceFramework):

	_svc_name_ = 'WebKit'
	_svc_display_name_ = 'WebKit Application Server'
	_svc_description_ = "This is the threaded application server" \
		" that belongs to the WebKit package" \
		" of the Webware for Python web framework."

	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.server = None
		# Fix the current working directory -- this gets initialized
		# incorrectly for some reason when run as an NT service.
		os.chdir(os.path.dirname(os.path.abspath(__file__)))

	def SvcStop(self):
		# Before we do anything, tell the SCM we are starting the stop process:
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		# And set running to 0 in the server. If it hasn't started yet, we'll
		# have to wait until it does.
		while self.server is None:
			time.sleep(1)
		self.server.initiateShutdown()

	def SvcDoRun(self):
		try:
			global workDir, webwareDir, libraryDirs, \
				runProfile, logFile, appServer, debug
			# Figure out the work directory and make it the current directory:
			if not workDir:
				workDir = os.path.dirname(os.path.abspath(__file__))
			os.chdir(workDir)
			workDir = os.path.curdir
			# Switch the output to the logfile specified above:
			if logFile:
				log = open(logFile, 'a', 1) # append, line buffered mode
			else:
				# Make all output go nowhere. Otherwise, print statements cause
				# the service to crash, believe it or not.
				log = open('nul', 'w')
			sys.stdout = sys.stderr = log
			sys.stdout.write('\n' + '-' * 68 + '\n\n')
			# By default, Webware is searched in the parent directory:
			if not webwareDir:
				webwareDir = os.pardir
			# Remove the package component in the name of this module,
			# because otherwise the package path would be used for imports, too:
			global __name__
			__name__ = __name__.split('.')[-1]
			# Check the validity of the Webware directory:
			sysPath = sys.path # memorize the standard Python search path
			sys.path = [webwareDir] # now include only the Webware directory
			# Check whether Webware is really located here
			from Properties import name as webwareName
			from WebKit.Properties import name as webKitName
			if webwareName != 'Webware for Python' or webKitName != 'WebKit':
				raise ImportError
			# Now assemble a new clean Python search path:
			path = [] # the new search path will be collected here
			absPath = [] # the absolute pathes
			absWebKitDir = os.path.abspath(os.path.join(webwareDir, 'WebKit'))
			for p in ['', webwareDir] + libraryDirs + sysPath:
				ap = os.path.abspath(p)
				if ap == absWebKitDir: # do not include the WebKit directory
					continue
				if ap not in absPath: # include every path only once
					path.append(p)
					absPath.append(ap)
			sys.path = path # set the new search path
			# Import the Profiler:
			from WebKit import Profiler
			Profiler.startTime = time.time()
			# Import the AppServer:
			appServerModule = __import__('WebKit.' + appServer, None, None, appServer)
			self.server = getattr(appServerModule, appServer)(workDir)
			if runProfile:
				print 'Profiling is on. See docstring in Profiler.py for more info.'
				print
				from profile import Profile
				profiler = Profile()
				Profiler.profiler = profiler
				Profiler.runCall(self.server.mainloop)
				Profiler.dumpStats()
			else:
				self.server.mainloop()
			self.server._closeThread.join()
		except Exception, error: # need to kill the sweeper thread somehow
			print error
			print 'Exiting AppServer...'
			if debug: # see the traceback from an exception
				tb = sys.exc_info()
				print tb[0]
				print tb[1]
				import traceback
				traceback.print_tb(tb[2])
			if self.server:
				self.server.running=0
				self.server.shutDown()
			raise


## Main ##

def main():
	win32serviceutil.HandleCommandLine(AppServerService)

if __name__=='__main__':
	main()

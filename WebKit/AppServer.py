#!/usr/bin/env python
"""
AppServer


FUTURE

	* Implement the additional settings that are commented out below.
"""

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),".."))

from Common import *
from Object import Object
from ConfigurableForServerSidePath import ConfigurableForServerSidePath
from Application import Application
from PlugIn import PlugIn
import sys, os


DefaultConfig = {
	'PrintConfigAtStartUp': 1,
	'Verbose':			  1,
	'PlugIns':			  ['../PSP']

	# @@ 2000-04-27 ce: None of the following settings are implemented
#	'ApplicationClassName': 'Application',
}


class AppServerError(Exception):
	pass


class AppServer(ConfigurableForServerSidePath, Object):

	## Init ##

	def __init__(self, path=None):
		self._startTime = time.time()
		ConfigurableForServerSidePath.__init__(self)
		Object.__init__(self)
		if path is None:
			path = os.path.dirname(__file__)  #os.getcwd()
		self._serverSidePath = os.path.abspath(path)
		self._verbose = self.setting('Verbose')
		self._plugIns = []
		self._reqCount = 0

		self.config() # cache the config
		self.printStartUpMessage()
		self._app = self.createApplication()
		self.loadPlugIns()

		self.running = 1
		


	def recordPID(self):
		"""
		Save the pid of the AppServer to a file name appserverpid.txt.
		"""
		pidfile = open(os.path.join(self._serverSidePath, "appserverpid.txt"),"w")

		if os.name == 'posix':
			pidfile.write(str(os.getpid()))
		else:
			try:
				import win32api
			except:
				print "win32 extensions not present.  Webkit Will not be able to detatch from the controlling terminal."
			if sys.modules.has_key('win32api'):
				pidfile.write(str(win32api.GetCurrentProcess()))

	def shutDown(self):
		"""
		Subclasses may override and normally follow this sequence:
			1. set self._shuttingDown to 1
			2. class specific statements for shutting down
			3. Invoke super's shutDown() e.g., AppServer.shutDown(self)
		"""
		print "Shutting down the AppServer"
		self._shuttingDown = 1
		self.running = 0
		self._app.shutDown()
		del self._plugIns
		del self._app
		print "AppServer has been shutdown"


	## Configuration ##

	def defaultConfig(self):
		return DefaultConfig

	def configFilename(self):
		return self.serverSidePath('Configs/AppServer.config')


	## Network Server ##

	def createApplication(self):
		''' Creates and returns an application object. Invoked by __init__. '''
		return Application(server=self)

	def printStartUpMessage(self):
		''' Invoked by __init__. '''
		print 'WebKit AppServer', self.version()
		print 'part of Webware for Python'
		print 'Copyright 1999-2000 by Chuck Esterbrook. All Rights Reserved.'
		print 'WebKit and Webware are open source.'
		print 'Please visit:  http://webware.sourceforge.net'
		print
		print 'Process id is', os.getpid()
		print
		if self.setting('PrintConfigAtStartUp'):
			self.printConfig()


	## Plug-ins ##

	def plugIns(self):
		''' Returns a list of the plug-ins loaded by the app server. Each plug-in is a python package. '''
		return self._plugIns

	def loadPlugIn(self, path):
		''' Loads and returns the given plug-in. May return None if loading was unsuccessful (in which case this method prints a message saying so). Used by loadPlugIns(). '''
		plugIn = None
		path = self.serverSidePath(path)
		try:
			plugIn = PlugIn(self, path)
			willNotLoadReason = plugIn.load()
			if willNotLoadReason:
				print '    Plug-in %s cannot be loaded because:\n    %s' % (path, willNotLoadReason)
				return None
			plugIn.install()
		except:
			import traceback
			traceback.print_exc(file=sys.stderr)
			self.error('Plug-in %s raised exception.' % path)
		return plugIn

	def loadPlugIns(self):
		"""
		A plug-in allows you to extend the functionality of WebKit without necessarily having to modify it's source. Plug-ins are loaded by AppServer at startup time, just before listening for requests. See the docs for PlugIn.py for more info.
		"""
		plugIns = self.setting('PlugIns')
		plugIns = map(lambda path: os.path.normpath(path), plugIns)

		# Scan each directory named in the PlugInDirs list.
		# If those directories contain Python packages (that
		# don't have a "dontload" file) then add them to the
		# plugs in list.
		for plugInDir in self.setting('PlugInDirs'):
			for filename in os.listdir(plugInDir):
				filename = os.path.normpath(os.path.join(plugInDir, filename))
				if os.path.isdir(filename) and \
				   os.path.exists(os.path.join(filename, '__init__.py')) and \
				   not os.path.exists(os.path.join(filename, 'dontload')) and \
				   os.path.basename(filename)!='WebKit' and \
				   filename not in plugIns:
					plugIns.append(filename)

		print 'Plug-ins list:', string.join(plugIns, ', ')

		# Now that we have our plug-in list, load them...
		for plugInPath in plugIns:
			plugIn = self.loadPlugIn(plugInPath)
			if plugIn:
				self._plugIns.append(plugIn)
		print


	## Access ##

	def version(self):
		# @@ 2000-07-10 ce: Resolve this with the fooVersion() methods in Application
		return '0.4.1'

	def application(self):
		return self._app

	def startTime(self):
		''' Returns the time the app server was started (as seconds, like time()). '''
		return self._startTime

	def numRequests(self):
		''' Return the number of requests received by this server since it was launched. '''
		return self._reqCount

	def isPersistent(self):
		raise SubclassResponsibilityError

	def serverSidePath(self, path=None):
		'''	Returns the absolute server-side path of the WebKit app server. If the optional path is passed in, then it is joined with the server side directory to form a path relative to the app server.
		'''
		if path:
			return os.path.normpath(os.path.join(self._serverSidePath, path))
		else:
			return self._serverSidePath


	## Warnings and Errors ##

	def warning(self, msg):
		# @@ 2000-04-25 ce: would this be useful?
		raise NotImplementedError

	def error(self, msg):
		"""
		Flushes stdout and stderr, prints the message to stderr and exits with code 1.
		"""
		sys.stdout.flush()
		sys.stderr.flush()
		sys.stderr.write('ERROR: %s\n' % msg)
		sys.stderr.flush()
		sys.exit(1)  # @@ 2000-05-29 ce: Doesn't work. Perhaps because of threads



def main():
	try:
		server = AppServer()
		return
		print "Ready"
		print
		print 'WARNING: There is nothing to do here with the abstract AppServer. Use one of the adapters such as WebKit.cgi (with ThreadedAppServer) or OneShot.cgi'
		server.shutDown()
	except Exception, exc:  # Need to kill the Sweeper thread somehow
		print 'Caught exception:', exc
		print "Exiting AppServer"
		server.shutDown()
		del server
		sys.exit()


def stop():
	pidfile = os.path.join(os.path.dirname(__file__),"appserverpid.txt")
	pid = int(open(pidfile,"r").read())
	#now what for windows?
	if os.name == 'posix':
		import signal
		os.kill(pid,signal.SIGINT)
	else:
		try:
			import win32process
		except:
			print "Win32 extensions not present.  Webkit cannot terminate the running process."
		if sys.modules.has_key('win32process'):
			win32process.TerminateProcess(pid,0)


if __name__=='__main__':
	main()

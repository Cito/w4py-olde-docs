#!/usr/bin/env python
"""
AppServer


FUTURE

	* Implement the additional settings that are commented out below.
"""


from Common import *
from Configurable import Configurable
from Application import Application
from PlugIn import PlugIn
import os, sys


DefaultConfig = {
	'PrintConfigAtStartUp': 1,
	'Verbose':			  1,
	'PlugIns':			  ['../PSP']

	# @@ 2000-04-27 ce: None of the following settings are implemented
#	'ApplicationClassName': 'Application',
}


class AppServerError(Exception):
	pass


class AppServer(Configurable):

	## Init ##

	def __init__(self):
		self._startTime = time.time()
		Configurable.__init__(self)
		self._verbose = self.setting('Verbose')
		self._plugIns = []
		self._reqCount = 0

		self.config() # cache the config
		self.printStartUpMessage()
		self._app = self.createApplication()
		self.loadPlugIns()

		self.running = 1


	def shutDown(self):
		"""
		Subclasses may override and normally follow this sequence:
			1. set self._shuttingDown to 1
			2. class specific statements for shutting down
			3. Invoke super's shutDown() e.g., AppServer.shutDown(self)
		"""

		self._shuttingDown = 1
		self.running = 0
		self._app.shutDown()
		del self._plugIns
		del self._app


	## Configuration ##

	def defaultConfig(self):
		return DefaultConfig

	def configFilename(self):
		return 'Configs/AppServer.config'


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
		''' Loads the given plug-in. Used by loadPlugIns(). '''
		try:
			plugIn = PlugIn(self, path)
			self._plugIns.append(plugIn)
			plugIn.load()
			plugIn.install()
		except:
			import traceback
			traceback.print_exc(file=sys.stderr)
			self.error('Plug-in %s raised exception.' % path)

	def loadPlugIns(self):
		"""
		A plug-in allows you to extend the functionality of WebKit without necessarily having to modify it's source. Plug-ins are loaded by AppServer at startup time, just before listening for requests. See the docs for PlugIn.py for more info.
		"""
		plugIns = self.setting('PlugIns')[:]
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
				   filename not in plugIns:
					plugIns.append(filename)

		print 'Plug-ins list:', string.join(plugIns, ', ')

		# Now that we have our plug-in list, load them...
		for plugInPath in plugIns:
			self.loadPlugIn(plugInPath)

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


if __name__=='__main__':
	main()

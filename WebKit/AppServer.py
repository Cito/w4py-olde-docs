#!/usr/bin/env python
'''
AppServer

The WebKit app server is a TCP/IP server that accepts requests, hands them
off to the Application and sends the request back over the connection.

The fact that the app server stays resident is what makes it so much quicker
than traditional CGI programming. Everything gets cached.


FUTURE

	* Implement the additional settings that are commented out below.
'''


from Common import *
from Configurable import Configurable
from Application import Application
from WebKitSocketServer import ThreadingTCPServer, ForkingTCPServer, TCPServer, BaseRequestHandler
from marshal import loads
import os, sys



DefaultConfig = {
	'PrintConfigAtStartUp': 1,
	'Verbose':              1,
	'Port':                 8086,
	'Multitasking':         'threading', # threading, forking, sequencing
	'PlugIns':              ['../PSP']

	# @@ 2000-04-27 ce: None of the following settings are implemented
#	'ApplicationClassName': 'Application',
#	'RequestQueueSize':     16,
#	'RequestBufferSize':    64*1024,
#	'SocketType':           'inet',      # inet, unix
}


TCPServerMap = {
	'thr': ThreadingTCPServer,
	'for': ForkingTCPServer,
	'seq': TCPServer
}


class AppServerError(Exception):
	pass


class WebKitAppServer(Configurable):
	'''
	Public Attrs - in the network server
		* wkApp: A public object that points to the application object. This is used by the request handler.

	Private Attrs
		* _addr:   The address of the server; a tuple containing server name and port.
		* _app:    The single instance of the Application.
		* _server: The TCP/IP server that takes the requests and dishes them out.
	'''

	request_queue_size = 16  # @@ 2000-04-27 ce: clean up

	## Init ##

	def __init__(self):
		Configurable.__init__(self)

		self._startTime = time.time()
		self._addr = None
		self._plugIns = []

		self.config() # cache the config
		self.printStartUpMessage()
		self._app = self.createApplication()
		self.loadPlugIns()
		self._server = self.createTCPServer()

		print 'OK'
		print


	## Configuration ##

	def defaultConfig(self):
		return DefaultConfig

	def configFilename(self):
		return 'Configs/AppServer.config'


	## Network Server ##

	def createApplication(self):
		''' Creates and returns an application object. Used by __init__. '''
		return Application(server=self)

	def addr(self):
		if self._addr is None:
			self._addr = ('', self.setting('Port'))
		return self._addr

	def createTCPServer(self):
		''' Creates and returns a TCP server object from the Python SocketServer module. Used by __init__. '''
		key = string.lower(self.setting('Multitasking'))[:3]
		if not TCPServerMap.has_key(key):
			self.error("Unknown Multitasking setting '%s' in configuration." % self.setting('Multitasking'))
		addr = self.addr()
		server = TCPServerMap[key](addr, RequestHandler)
		open('address.text', 'w').write('%s:%d' % (addr[0], addr[1]))
		# @@ 2000-04-27 ce: close ^^
		print 'Listening at', addr
		server.wkApp = self._app  # for use by the request handler
		server.wkVerbose = self.setting('Verbose')
		return server

	def printStartUpMessage(self):
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

	def loadPlugIn(self, name, dir):
		''' Loads the given plug-in. Used by loadPlugIns(). Really invokes _loadPlugIn() and catches exceptions in order to invoke self.error(). '''
		try:
			self._loadPlugIn(name, dir)
		except:
			import traceback
			traceback.print_exc(file=sys.stderr)
			self.error('Plug-in %s raised exception.' % name)

	def _loadPlugIn(self, name, dir):
		''' The "real" implementation of loadPlugIn(). '''
		print 'Plug-in: %s in %s' % (name, dir)

		# Update sys.path
		if not dir in sys.path:
			sys.path.append(dir)

		# Import the package
		plugIn = __import__(name, globals(), [], [])

		# Add to our plugIns list
		self._plugIns.append(plugIn)

		# Install the package
		if not hasattr(plugIn, 'InstallInWebKit'):
			raise AppServerError, "Plug-in '%s' in '%s' has no InstallInWebKit() function." % (name, dir)
		plugIn.InstallInWebKit(self)

	def loadPlugIns(self):
		# @@ 2000-05-21 ce: We should really have an AddPlugIns and RemovePlugIns setting
		''' A plug-in allows you to extend the functionality of WebKit without necessarily having to modify it's source.

		* Plug-ins are loaded by AppServer at startup time, just before listening for requests.
		* A plug-in is a Python package. Therefore, it is a directory containing an __init__.py file.
		* The directory of the package is added to sys.path and the package is imported.
		* The __init__.py must contain a function, InstallInWebKit(appServer). AppServer invokes this at start-up so that the plug-in can do what it needs to.
		'''


		for plugIn in self.setting('PlugIns'):
			dir, name = os.path.split(plugIn)
			self.loadPlugIn(name, dir)


	## Misc ##

	def setRequestQueueSize(self, value):
		assert value>=1
		self.__class__.request_queue_size = value

	def version(self):
		return '0.3'

	def serve(self):
		''' Starts serving requests and does so indefinitely. Sends serve_forever() to the TCP server. '''
		self._server.serve_forever()

	def application(self):
		return self._app

	def startTime(self):
		''' Returns the time the app server was started (as seconds, like time()). '''
		return self._startTime

	def numRequests(self):
		''' Return the number of requests received by this server since it was launched. '''
		return self._server.num_requests


	## Warnings and Errors ##

	def warning(self, msg):
		# @@ 2000-04-25 ce: would this be useful?
		raise NotImplementedError

	def error(self, msg):
		''' Flushes stdout and stderr, prints the message to stderr and exits with code 1. '''
		sys.stdout.flush()
		sys.stderr.flush()
		sys.stderr.write('ERROR: %s\n' % msg)
		sys.stderr.flush()
		sys.exit(1)  # @@ 2000-05-29 ce: Doesn't work. Perhaps because of threads


class RequestHandler(BaseRequestHandler):

	def handle(self):
		#JSL-Looking for memory leak
		import sys
		# according to BaseRequestHandler docs, we have access to self.[request, client_address, server]
		verbose = self.server.wkVerbose

		startTime = time.time()
		if verbose:
			print 'BEGIN REQUEST'
			print time.asctime(time.localtime(startTime))
		conn = self.request
		if verbose:
			print 'receiving request from', conn
		recv = conn.recv
		BUFSIZE = 8*1024
		data = []
		while 1:
			chunk = recv(BUFSIZE)
			if not chunk:
				break
			data.append(chunk)
		data = string.join(data, '')
		if verbose:
			print 'received %d bytes' % len(data)
		if data:
			dict = loads(data)
			if verbose:
				print 'request has keys:', string.join(dict.keys(), ', ')

			transaction = self.server.wkApp.dispatchRawRequest(dict)
			results = transaction.response().contents()

			if verbose:
				print 'about to send %d bytes' % len(results)
			conn.send(results)
			if verbose:
				print 'sent.'
		else:
			print '! empty request. not replying.'
			# @@ 2000-05-08 ce: should we do something better here?
		conn.close()
		if verbose:
			print 'connection closed.'
			print '%0.2f secs' % (time.time() - startTime)
			print 'END REQUEST'
			print

		transaction.die()


def main():
	server = WebKitAppServer()
	try:
		server.serve()
	except KeyboardInterrupt: #Need to kill the Sweeper thread somehow
		print "Exiting AppServer"
		sys.exit()


if __name__=='__main__':
	main()

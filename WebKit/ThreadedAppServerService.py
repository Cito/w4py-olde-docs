#!/usr/bin/env python
"""
ThreadedAppServerService

For general notes, see ThreadedAppServer.py.

This version of the app server is a threaded app server that runs as
a Windows NT Service.  This means it can be started and stopped from
the Control Panel or from the command line using "net start" and
"net stop", and it can be configured in the Control Panel to
auto-start when the machine boots.

This requires the win32all package to have been installed.

To see the options for installing, removing, starting, and stopping
the service, just run this program with no arguments.  Typical usage is
to install the service to run under a particular user account and startup
automatically on reboot with

python ThreadedAppServerService.py --username mydomain\myusername --password mypassword --startup auto install

Then, you can start the service from the Services applet in the Control Panel,
where it will be listed as "WebKit Threaded Application Server".  Or, from
the command line, it can be started with either of the following commands:

net start WebKit
python ThreadedAppServerService.py start

The service can be stopped from the Control Panel or with:

net stop WebKit
python ThreadedAppServerService.py stop

And finally, to uninstall the service, stop it and then run:

python ThreadedAppServerService.py remove

FUTURE
	* This file shares a lot of code with ThreadedAppServer.py --
	  instead it should inherit from ThreadedAppServer and have
	  very little code of its own.
	* Have an option for sys.stdout and sys.stderr to go to a logfile instead
	  of going nowhere.
	* Optional NT event log messages on start, stop, and errors.
	* Allow the option of installing multiple copies of WebKit with
	  different configurations and different service names.
	* Figure out why I need the Python service hacks marked with ### below.
	* Allow it to work with wkMonitor, or some other fault tolerance
	  mechanism.
"""

# ### Fix the current working directory -- this gets initialized incorrectly
# for some reason when run as an NT service.
import os
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass


from Common import *
from AppServer import AppServer
from marshal import dumps, loads
import os, sys
from threading import Lock, Thread
import Queue
import select
import socket
from WebUtils.WebFuncs import RequestURI


DefaultConfig = {
	'Port':                 8086,
	'ServerThreads':        10,

	# @@ 2000-04-27 ce: None of the following settings are implemented
#	'RequestQueueSize':     16,
#	'RequestBufferSize':    64*1024,
#	'SocketType':           'inet',      # inet, unix
}



#Below used with the RestartApplication function
#ReStartLock=Lock()
#ReqCount=0


class ThreadedAppServer(AppServer):
	"""
	"""

	## Init ##

	def __init__(self):
		AppServer.__init__(self)
		self._addr = None
		self._poolsize = self.setting('ServerThreads')
		self.threadPool = []
		self.requestQueue = Queue.Queue(self._poolsize*2) # twice the number of threads we have
		self.rhQueue = Queue.Queue(self._poolsize) # same size as threadQueue

		self.mainsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		addr = self.address()
		self.mainsocket.bind(addr)
		print "Listening on", addr
		open('address.text', 'w').write('%s:%d' % (addr[0], addr[1]))
		self.monitorPort=addr[1]-1

		out = sys.stdout
		out.write('Creating %d threads' % self._poolsize)
		for i in range(self._poolsize): #change to threadcount
			t = Thread(target=self.threadloop)
			t.start()
			self.threadPool.append(t)
			out.write(".")
			out.flush()
		out.write("\n")

		self.mainsocket.listen(64) # @@ 2000-07-10 ce: hard coded constant should be a setting

	def isPersistent(self):
		return 1

	def mainloop(self, monitor=None, timeout=1, hStopEvent=None):

		inputsockets = [self.mainsocket,]
		if monitor:
			inputsockets.append(monitor.insock)

		while 1:
			# Check if the service has been requested to stop
			if win32event.WaitForSingleObject(hStopEvent, 0) == win32event.WAIT_OBJECT_0:
				self.running = 0

			# Shut down the app server if we're no longer running			
			if not self.running:
				self.shutDown()
				break

			#block for timeout seconds waiting for connections
			input, output, exc = select.select(inputsockets,[],[],timeout)
			for sock in input:
				if sock.getsockname()[1] == self.monitorPort:
					client,addr = sock.accept()
					monitor.activate(client)
					self.requestQueue.put(monitor)
				else:
					self._reqCount = self._reqCount+1
					rh = None
					client,addr = sock.accept()
					try:
						rh=self.rhQueue.get_nowait()
					except Queue.Empty:
						rh = RequestHandler(self)
					rh.activate(client)
					self.requestQueue.put(rh)

	def threadloop(self):
		self.initThread()
		try:
			while self.running:
				try:
					rh=self.requestQueue.get()
					if rh == None: #None means time to quit
						break
					rh.handleRequest()
					rh.close()
##					try:
##						self.rhQueue.put(rh)
##					except Queue.Full:
##						#print ">> rhQueue Full"
##						pass				#do I want this?
				except Queue.Empty:
					pass
		finally:
			self.delThread()

	def initThread(self):
		''' Invoked immediately by threadloop() as a hook for subclasses. This implementation does nothing and subclasses need not invoke super. '''
		pass

	def delThread(self):
		''' Invoked immediately by threadloop() as a hook for subclasses. This implementation does nothing and subclasses need not invoke super. '''
		pass


	def shutDown(self):
		self._shuttingDown = 1
		self.mainsocket.close()
		for i in range(self._poolsize):
			self.requestQueue.put(None)#kill all threads
		for i in self.threadPool:
			i.join()
		AppServer.shutDown(self)



	## Network Server ##

	def address(self):
		if self._addr is None:
			self._addr = (self.setting('Host'), self.setting('Port'))
		return self._addr


	## Misc ##

	def setRequestQueueSize(self, value):
		assert value>=1
		self.__class__.request_queue_size = value


class Monitor:

	def __init__(self, server):
		self.server = server
		self.port = server.monitorPort
		self.insock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.insock.bind([server.address()[0],server.address()[1]-1])
		self.insock.listen(1)

	def activate(self, socket):
		self.sock = socket

	def close(self):
		self.sock = None

	def handleRequest(self):

		verbose = self.server._verbose

		startTime = time.time()
		if verbose:
			print 'BEGIN REQUEST'
			print time.asctime(time.localtime(startTime))
		conn = self.sock
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

		if data == "STATUS":
			conn.send(str(self.server._reqCount))
		conn.close()



class RequestHandler:

	def __init__(self, server):
		self.server = server

	def activate(self, socket):
		self.sock = socket

	def close(self):
		self.sock = None
		self.server.rhQueue.put(self)

	def handleRequest(self):

		verbose = self.server._verbose

		startTime = time.time()
		if verbose:
			print 'BEGIN REQUEST'
			print time.asctime(time.localtime(startTime))
		conn = self.sock
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
				if dict.has_key('environ'):
					requestURI = RequestURI(dict['environ'])
				else:
					requestURI = None
				print 'request uri =', requestURI

		transaction = self.server._app.dispatchRawRequest(dict)
		rawResponse = dumps(transaction.response().rawResponse())


		reslen = len(rawResponse)
		sent = 0
		while sent < reslen:
			sent = sent + conn.send(rawResponse[sent:sent+8192])

		conn.close()

		if verbose:
			print 'connection closed.'
			print '%0.2f secs' % (time.time() - startTime)
			print 'END REQUEST'
			print

		transaction._application=None
		transaction.die()
		del transaction

	def restartApp(self):
		"""
		Not used
		"""
		if self.server.num_requests> 200:
			print "Trying to get lock"
			ReStartLock.acquire()
			if self.server.num_requests> 200: #check again to make sure another thread didn't do it
				print "Restarting Application"
				currApp=self.server.wkApp
				wkAppServer=currApp._server
				newApp = wkAppServer.createApplication()
				newApp._sessions = currApp._sessions
				wkAppServer._app=newApp
				self.server.wkApp=newApp
				for i in currApp._factoryList:
					currApp._factoryList.remove(i)
				for i in currApp._factoryByExt.keys():
					currApp._factoryByExt[i]=None
				currApp._canFactory=None
				wkAppServer._plugIns=[]
				wkAppServer.loadPlugIns()


				self.server.num_requests=0
				print "Refs to old App=",sys.getrefcount(currApp)
				currApp=None
			ReStartLock.release()



import win32serviceutil
import win32service
import win32event

class ThreadedAppServerService(win32serviceutil.ServiceFramework):
	_svc_name_ = 'WebKit'
	_svc_display_name_ = 'WebKit Threaded Application Server'

	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		# ### Make all output go nowhere -- otherwise, print statements cause
		# the service to crash, believe it or not.
		class NullFile:
			def write(self, x):
				pass
			def flush(self):
				pass
		import sys
		sys.stdout = sys.stderr = NullFile()
		# Create an event which we will use to wait on.
		# The "service stop" request will set this event.
		self.hStopEvent = win32event.CreateEvent(None, 0, 0, None)

	def SvcStop(self):
		# Before we do anything, tell the SCM we are starting the stop process
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		# And set my event.
		win32event.SetEvent(self.hStopEvent)

	def SvcDoRun(self):
		try:
			server = None
			server = ThreadedAppServer()
			server.mainloop(hStopEvent=self.hStopEvent)
		except Exception, e: #Need to kill the Sweeper thread somehow
			print e
			print "Exiting AppServer"
			if 0: #See the traceback from an exception
				tb = sys.exc_info()
				print tb[0]
				print tb[1]
				import traceback
				traceback.print_tb(tb[2])
			if server:
				server.running=0
				server.shutDown()
			raise

if __name__=='__main__':
	win32serviceutil.HandleCommandLine(ThreadedAppServerService)
	
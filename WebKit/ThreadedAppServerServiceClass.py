# This file is very similar to ThreadedAppServer.py -- any bugfixes made there
# should probably also be made here, and vice-versa.  The two files really
# ought to be merged together at some point, but I'm loathe to put win32-specific
# stuff into ThreadedAppServer.py.

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
import win32event

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
		self.rhQueue = Queue.Queue(0) # This will grow to a limit of the number of
		                              # threads plus the size of the requestQueue plus one.
		                              # But it's easier to just let it be unlimited.

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



	
#!/usr/bin/env python
"""
AppServer

The WebKit app server is a TCP/IP server that accepts requests, hands them
off to the Application and sends the request back over the connection.

The fact that the app server stays resident is what makes it so much quicker
than traditional CGI programming. Everything gets cached.


FUTURE

	* Implement the additional settings that are commented out below.
"""


from Common import *
from AppServer import AppServer
from marshal import dumps, loads
import os, sys
from threading import Lock, Thread
import Queue
import select
import socket
import threading
import time
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

#Need to know this value for communications
#Note that this limits the size of the dictionary we receive from the AppServer to 2,147,483,647 bytes
int_length = len(dumps(int(1)))

server = None

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
		self.recordPID()
		print "Ready\n"

	def isPersistent(self):
		return 1

	def mainloop(self, monitor=None, timeout=1):
		from errno import EINTR

		inputsockets = [self.mainsocket,]
		if monitor:
			inputsockets.append(monitor.insock)

		while 1:
			if not self.running:
				return

			#block for timeout seconds waiting for connections
			try:
				input, output, exc = select.select(inputsockets,[],[],timeout)
			except select.error, v:
				# if the error is EINTR/interrupt, then self.running should be set to 0 and
				# we'll exit on the next loop
				if v[0] == EINTR or v[0]==0: break
				else: raise
			if not self.running:
				return

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
			while 1:
				try:
					rh=self.requestQueue.get()
					if rh == None: #None means time to quit
						break
					if self.running:
						rh.handleRequest()
					rh.close()
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
		print "Shutting Down Threaded AppServer"
		self.running = 0
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

		if data == 'QUIT':
			self.server.shutDown()
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
		verbose = 1
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

		chunk = ''
		while len(chunk) < int_length:
			chunk = chunk + recv(int_length)
		dict_length = loads(chunk)
		if type(dict_length) != type(1):
			conn.close()
			print "Error: Invalid AppServer protocol"
			return 0

		chunk = ''
		missing = dict_length
		while missing > 0:
			chunk = chunk + recv(missing)
			missing = dict_length - len(chunk)

		dict = loads(chunk)
		if verbose:
			chucklen1 = len(chunk)

		while 1:
			chunk = recv(BUFSIZE)
			if not chunk:
				break
			data.append(chunk)
		data = string.join(data, '')
		conn.shutdown(0)

		dict['input'] = data

		if dict:
			if verbose:
				print 'request has keys:', string.join(dict.keys(), ', ')
				if dict.has_key('environ'):
					requestURI = RequestURI(dict['environ'])
				else:
					requestURI = None
				print 'request uri =', requestURI

		transaction = self.server._app.dispatchRawRequest(dict)
		rawResponse = transaction.response().rawResponse()


		sent = 0

		self._buffer = ''
		for item in rawResponse['headers']:
			self._buffer = self._buffer + item[0] + ": " + str(item[1]) + "\n"

		self._buffer = self._buffer + "\n" + rawResponse['contents']


		reslen = len(self._buffer)
		while sent < reslen:
			sent = sent + conn.send(self._buffer[sent:sent+8192])

		conn.shutdown(1)
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



def run(useMonitor=0):
	global server
	try:
		server = None
		server = ThreadedAppServer()
		if useMonitor:
			monitor = Monitor(server)
		else:
			monitor = 0
		# On NT, run mainloop in a different thread because it's not safe for
		# Ctrl-C to be caught while manipulating the queues.
		# It's not safe on Linux either, but there, it appears that Ctrl-C
		# will trigger an exception in ANY thread, so this fix doesn't help.
		if os.name == 'nt':
			t = threading.Thread(target=server.mainloop, args=(monitor,))
			t.start()
			try:
				while server.running:
					time.sleep(1.0)
			except KeyboardInterrupt:
				pass
			server.running = 0
			t.join()
		else:
			try:
				server.mainloop(monitor)
			except KeyboardInterrupt, e:
				server.shutDown()
	except Exception, e: #Need to kill the Sweeper thread somehow
		import traceback
		traceback.print_exc(file=sys.stderr)
		#print e
		print
		print "Exiting AppServer"
		if server.running:
			server.running=0
			server.shutDown()
		sys.exit()


def shutDown(arg1,arg2):
	global server
	print "Shutdown Called"
	server.shutDown()

import signal
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)



usage = """
The AppServer is the main process of WebKit.  It handles requests for servlets from webservers.
ThreadedAppServer takes the following command line arguments:
-stop:  Stop the currently running Apperver.
If AppServer is called with no arguments, it will start the AppServer and record the pid of the process in appserverpid.txt
"""


def main(args):
	if len(args)>1:
		if args[1] == "-monitor":
			print "Enabling Monitoring"
			run(useMonitor=1)
		elif args[1] == "-stop":
			import AppServer
			AppServer.stop()
		else:
			print usage
	else:
		if 0:
			import profile
			profile.run("main()", "profile.txt")
		else:
			run(useMonitor=0)

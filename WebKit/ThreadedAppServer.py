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

	def mainloop(self, monitor, timeout=1):

		inputsockets = [self.mainsocket,]
		if monitor:
			inputsockets.append(monitor.insock)

		while 1:
			if not self.running:#this won't happen for now, the only way to kill this thread is with KeyboardInterrupt
				self.mainsocket.close()
				for i in range(self._poolsize):
					self.requestQueue.put(None)#kill all threads
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


##def main():
##	try:
##		server = None
##		server = ThreadedAppServer()
##		print 'Ready\n'
##		server.mainloop()
##	except Exception, e: #Need to kill the Sweeper thread somehow
##		print e
##		print "Exiting AppServer"
##		if server:
##			server.shutDown()
##		sys.exit()

def main(monitor = 0):
	try:
		server = None
		server = ThreadedAppServer()
		if monitor:
			monitor = Monitor(server)
		server.mainloop(monitor)
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
		sys.exit()
		raise Exception()


if __name__=='__main__':
	import sys
	if len(sys.argv) > 1 and sys.argv[1] == "-monitor":
		print "Using Monitor"
		main(1)
	else:
		if 0:
			import profile
			profile.run("main()","profile.txt")
		else:
			main(0)

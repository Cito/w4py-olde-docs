#!/usr/bin/env python
"""
Version of AppServer that uses threads and the asyncore module.
"""


from AppServer import AppServer
from Application import Application
from marshal import dumps, loads
import os, sys
from threading import Lock, Thread
import Queue
import select
import socket
import asyncore
from WebUtils.WebFuncs import RequestURI

try:
	from SelectRelease import SelectRelease
	MainRelease=SelectRelease()
except:
	MainRelease = lambda:()

debug = 0

#Need to know this value for communications
#Note that this limits the size of the dictionary we receive from the AppServer to 2,147,483,647 bytes
int_length = len(dumps(int(1)))

class AsyncThreadedAppServer(asyncore.dispatcher, AppServer):
	"""
	"""
	def __init__(self):
		AppServer.__init__(self)

		self._addr = None
		self._poolsize=self.setting('ServerThreads')

		self.threadPool=[]
		self.requestQueue=Queue.Queue(self._poolsize*5) #5 times the number of threads we have
		self.rhQueue=Queue.Queue(0)#must be larger than requestQueue, just make it no limit, and limit the number that can be created
		self._maxRHCount = self._poolsize * 10
		self.rhCreateCount = 0

		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		addr = self.address()
		self.bind(addr)
		print "Listening on", addr
		open('address.text', 'w').write('%s:%d' % (addr[0], addr[1]))

		self.running=1

		out = sys.stdout
		out.write('Creating %d threads' % self._poolsize)
		for i in range(self._poolsize): #change to threadcount
			t = Thread(target=self.threadloop)
			t.start()
			self.threadPool.append(t)
			out.write(".")
			out.flush()
		out.write("\n")

	    #self.asyn_thread = Thread(target=self.asynloop)
	    #self.asyn_thread.start()

		self.setRequestHandlerClass(RequestHandler)

		self.listen(self._poolsize*2) # @@ 2000-07-14 ce: hard coded constant should be a setting
		print "Ready\n"


	def isPersistent(self):
		return 1


	def setRequestHandlerClass(self, requestHandlerClass):
		self._requestHandlerClass = requestHandlerClass

	def handle_accept(self):
		"""
		This is the function that starts the request processing cycle.  When asyncore senses a write on the main socket, it calls this function.  We then accept the connection, and hand it off to a RequestHandler instance by calling the RequestHandler instance's activate method.  When we call that activate method, the RH registers itself with asyncore by calling set_socket, so that asyncore now will include that socket, and thus the RH, in it's network select loop.
		"""
		rh = None
		try:
			rh=self.rhQueue.get_nowait()
		except Queue.Empty:
			if self.rhCreateCount < self._maxRHCount:
				rh = self._requestHandlerClass(self)
				self.rhCreateCount = self.rhCreateCount + 1
			else:
		#rh = self.rhQueue.get() #block - No Don't, cause then nothing else happens, we're frozen
				print "Refusing Connection"
				return
		self._reqCount = self._reqCount+1
		conn,addr = self.accept()
		conn.setblocking(0)
		rh.activate(conn, addr)

	def readable(self):
		return self.accepting

	def writable(self):
		return 0

	def handle_connect(self):
		pass

	def log(self, message):
		pass

	def asynloop(self):
		"""
		Not used currently
		"""
		while self.running:
		#print "asyncore loop"
		    asyncore.loop()

	def address(self):
		if self._addr is None:
			self._addr = (self.setting('Host'), self.setting('Port'))
		return self._addr




	def threadloop(self):
		"""
		Try to get a RequestHandler instance off the requestQueue and process it.
		"""

		self.initThread()
		try:
			while self.running:
				try:
					rh=self.requestQueue.get()
					if rh == None: #None means time to quit
						break
					rh.handleRequest()      #this is all there is to it
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
		"""
		Cleanup when being shut down.
		"""
		self._app.shutDown()
		#self.mainsocket.close()
		for i in range(self._poolsize):
			self.requestQueue.put(None)#kill all threads
		for i in self.threadPool:
			i.join()
		del self._plugIns[:]

		del self._app



import string, time

class RequestHandler(asyncore.dispatcher):
	"""
	Has the methods that process the request.
	An instance of this class is activated by AppServer.  When activated, it is listening for the request to come in.  asyncore will call handle_read when there is data to be read.  ONce all the request has been read, it will put itself in the requestQueue to be picked up by a thread and processed by calling handleRequest. Once the processing is complete, the thread drops the instance and tries to find another one.  This instance notifies asyncore that it is ready to send.
	"""


	def __init__(self, server):
		self.server=server
		self.have_request = 0
		self.have_response = 0
		self.reqdata=[]
		self._buffer = ''

	def handleRequest(self):
		#check for status message
		if self.reqdata == "STATUS":
			self._buffer = str(self.server._reqCount)
			self.have_response = 1
			return

		verbose = self.server._verbose
		verbose = 1

		startTime = time.time()
		if verbose:
			print 'BEGIN REQUEST'
			print time.asctime(time.localtime(startTime))

		if verbose:
			print 'receiving request from', self.socket

		while not self.have_request:
			print ">> Should always have request before we get here"
			time.sleep(0.01)

		if verbose:
			print 'received %d bytes' % len(self.reqdata)
		if self.reqdata:
			dict_length = loads(self.reqdata[:int_length])
			dict = loads(self.reqdata[int_length:int_length+dict_length])
			dict['input'] = self.reqdata[int_length+dict_length:]
			if verbose:
				print 'request has keys:', string.join(dict.keys(), ', ')
				if dict.has_key('environ'):
					requestURI = RequestURI(dict['environ'])
				else:
					requestURI = None
				print 'request uri =', requestURI


		transaction = self.server._app.dispatchRawRequest(dict)


		rawResponse = transaction.response().rawResponse()

		for item in rawResponse['headers']:
			self._buffer = self._buffer + item[0] + ":" + str(item[1]) + "\n"
		
		self._buffer = self._buffer + "\n" + rawResponse['contents']
		
		self.have_response = 1

		transaction._application=None
		transaction.die()
		del transaction
		MainRelease.release()

	def activate(self, socket, addr):
		self.set_socket(socket)
		self._buffer=''
		self.active = 1

	def readable(self):
		return self.active and not self.have_request

	def writable(self):
		return self.have_response

	def handle_connect(self):
		pass

	def handle_read(self):
		if self.have_request:
			print ">> Received Spurious Write"
			return
		data = self.recv(8192) #socket is non-blocking
		if data:
			self.reqdata.append(data)
		else: #we have it all
			self.reqdata = string.join(self.reqdata,'')
			self.have_request=1
			self.server.requestQueue.put(self)



	def handle_write(self):
		if not self.have_response:
			print ">> Handle write called before response is ready\n"
			return
		sent = self.send(self._buffer)
		self._buffer = self._buffer[sent:]
		if len(self._buffer) == 0:
			self.socket.shutdown(1)
			self.close()
			#For testing
		if debug:
			sys.stdout.write(".")
			sys.stdout.flush()

	def close(self):
		#print ">>Close Called"
		self.recycle()

	def handle_close(self):
		print ">>Handling Close"
		#self.recycle()
		
	def recycle(self):
		#print "Recycling\n"
		self.active = 0
		self.have_request = 0
		self.have_response = 0
		self.reqdata=[]
		asyncore.dispatcher.close(self)
		self.server.rhQueue.put(self)		

	def log(self, message):
		pass

class Monitor(asyncore.dispatcher):
	"""
	This is a dispatch class that handles requests on the monitor port.
	"""

	def __init__(self, server):
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		addr = ((server.address()[0],server.address()[1]-1))
		self.bind(addr)
		self.listen(5)
		self.server = server

	def handle_accept(self):
		rh = None
		try:
			rh=self.server.rhQueue.get_nowait()
		except Queue.Empty:
			if self.server.rhCreateCount < self.server._maxRHCount:
				rh = RequestHandler(self.server)
				self.server.rhCreateCount = self.server.rhCreateCount + 1
			else:
				print "Refusing Connection"
				return
		conn,addr = self.accept()
		conn.setblocking(0)
		rh.activate(conn)

	def log(self, message):
		pass



def main(monitor = 0):
	try:
		server = None
		server = AsyncThreadedAppServer()
		if monitor:
			monitor = Monitor(server)
		asyncore.loop()
	except Exception, e: #Need to kill the Sweeper thread somehow
		print e
		print "Exiting AppServer"
		if 1: #See the traceback from an exception
			tb = sys.exc_info()
			print tb[0]
			print tb[1]
			import traceback
			traceback.print_tb(tb[2])
		if server:
			server.running=0
			server.shutDown()
		#return
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

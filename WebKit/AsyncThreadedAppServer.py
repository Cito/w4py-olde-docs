#!/usr/bin/env python
"""
Version of AppServer that uses threads and the asyncore module.
"""


from AppServer import AppServer
from Application import Application
from marshal import dumps, loads
import os, sys
from threading import Lock, Thread, Event, RLock
import Queue
import select
import socket
import asyncore
import string
import time
import exceptions
from WebUtils import Funcs

try:
	from SelectRelease import SelectRelease
	MainRelease=SelectRelease()
except:
	MainRelease = lambda:()

debug = 0
global server
server = None
global monitor
monitor = 0


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
		open(self.serverSidePath('address.text'), 'w').write('%s:%d' % (addr[0], addr[1]))

		self.running=1

		out = sys.stdout
		out.write('Creating %d threads' % self._poolsize)
		for i in range(self._poolsize): #change to threadcount
			t = Thread(target=self.threadloop)
##			t.setDaemon(1)  #if the thread is a daemon, then thread.join appears to return immediately
			t.start()
			self.threadPool.append(t)
			out.write(".")
			out.flush()
		out.write("\n")

		self.setRequestHandlerClass(RequestHandler)

		self.listen(1024) # @@ 2000-07-14 ce: hard coded constant should be a setting

		self.recordPID()

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
		print "AppServer: Shutting Down AsyncThreadedAppServer"
		self.running=0
		self.close()
		for i in range(self._poolsize):
			self.requestQueue.put(None) #tells threads to exit, in addition to the self.running=0
		for i in self.threadPool:
			i.join()  #don't continue 'till we have all the threads
##		print "Socket Count: %s" % len(asyncore.socket_map)
##		for i in asyncore.socket_map.keys():
##			print asyncore.socket_map[i]
		if len(asyncore.socket_map) > monitor+1:
			time.sleep(5)  #try to allow for connections to close, but don't wait too long.  Sometimes, they never close?
##		print "Socket Count: %s" % len(asyncore.socket_map)
		asyncore.close_all()
		AppServer.shutDown(self)
		print "AppServer: All Services have been shutdown"



from WebKit.ASStreamOut import ASStreamOut
class ASTASStreamOut(ASStreamOut):
	"""
	This class handles a response stream for AsyncThreadedAppServer.
	"""
	def __init__(self, trigger):
		ASStreamOut.__init__(self)
		self._lock = RLock() #we need an reentrant lock because the write method uses the lock, but it can also call flush, which also uses the lock
		self._trigger = trigger

	def close(self):
		self.flush()
		ASStreamOut.close(self)
		self._trigger.release()

	def writable(self):
		"""
		Called by asyncore to ask if we want to write data
		"""
		if debug: print "writeable called with self._comm=%s and len(buffer)=%s"%(self._committed, len(self._buffer))
		if self._closed: return 1
		return self._committed and self._buffer

	def flush(self):
		if debug: print "ASTASStreanOut Flushing"
		self._lock.acquire()
		ASStreamOut.flush(self)
		self._lock.release()
		if self._committed:
			self._trigger.release()
		
	def write(self, charstr):
		self._lock.acquire()
		ASStreamOut.write(self, charstr)
		self._lock.release()

	def pop(self, count):
		self._lock.acquire()
		ASStreamOut.pop(self, count)
		self._lock.release()


from ATASStreamIn import ATASStreamIn

class RequestHandler(asyncore.dispatcher):
	"""
	Has the methods that process the request.
	An instance of this class is activated by AppServer.  When activated, it is listening for the request to come in.  asyncore will call handle_read when there is data to be read.  Once all the request has been read, it will put itself in the requestQueue to be picked up by a thread and processed by calling handleRequest. Once the processing is complete, the thread drops the instance and tries to find another one.  This instance notifies asyncore that it is ready to send.
	"""


	def __init__(self, server):
		self.server=server
##		self.have_request = 0
		self.have_response = 0
		self._strmOut = None
		self.readfile = ATASStreamIn(self,8192)
		
	def handleRequest(self):

		dictlen = loads(self.readfile.read(int_length))

		dict = loads(self.readfile.read(dictlen))
		
##		check for status message
   		if dict.get('format') == "STATUS":
   			self._strmOut.write( str(self.server._reqCount))
			self._strmOut.commit()
   			self._strmOut.close()
			time.sleep(1)
   			return
   		if dict.get('format') == 'QUIT':
   			self._strmOut.write('OK')
			self._strmOut.commit()
   			self._strmOut.close()
   			time.sleep(2)
   			self.server.initiateShutdown()
   			return

			
		verbose = self.server._verbose

		startTime = time.time()
		if verbose:
			print 'BEGIN REQUEST'
			print time.asctime(time.localtime(startTime))

		if verbose:
			print 'receiving request from', self.socket

#		while not self.have_request:
#			print ">> Should always have request before we get here"
#			time.sleep(0.01)

#		if verbose:
#			print 'received %d bytes' % len(self.reqdata)
		if 1:
##			dict_length = loads(self.reqdata[:int_length])
##			dict = loads(self.reqdata[int_length:int_length+dict_length])
##			dict['input'] = self.reqdata[int_length+dict_length:]
			dict['input'] = self.readfile
			if verbose:
				print 'request has keys:', string.join(dict.keys(), ', ')
				if dict.has_key('environ'):
					requestURI = Funcs.requestURI(dict['environ'])
				else:
					requestURI = None
				print 'request uri =', requestURI


		transaction = self.server._app.dispatchRawRequest(dict, self._strmOut)
		self._strmOut.close()


		transaction._application=None
		transaction.die()
		del transaction
		MainRelease.release()



	def activate(self, socket, addr):
		self.set_socket(socket)
		self.active = 1
		self._strmOut = ASTASStreamOut(MainRelease)


	def readable(self):
		return self.active and self.readfile.canRecv()
##		return self.active and not self.have_request

	def writable(self):
		return self.active and self._strmOut.writable()

	def handle_connect(self):
		pass

	def handle_read(self):
##		if self.have_request:
##			print ">> Received Spurious Write"
##			return
##		data = self.recv(8192) #socket is non-blocking
##		if data:
##			self.reqdata.append(data)
##		else: #we have it all
##			self.reqdata = string.join(self.reqdata,'')
##			self.have_request=1
##			self.server.requestQueue.put(self)
		self.readfile.recv()



	def handle_write(self):
		try:
			sent = self.send(self._strmOut._buffer)
		except socket.error, e:
			if e[0] == 32: #bad file descriptor
				self.close()
				return
		self._strmOut.pop(sent)
		
		 #if the servlet has returned and there is no more data in the buffer
		if self._strmOut._closed and not self._strmOut._buffer: 
			self.close()
			#For testing
		elif self._strmOut._buffer:
			MainRelease.release() #let's send the rest
		if debug:
			sys.stdout.write(".")
			sys.stdout.flush()

	def close(self):
		if debug: print "Socket closing"
		self.socket.shutdown(1)
		self.recycle()

	def handle_close(self):
		pass
		#print ">>Handling Close"
		#self.recycle()

	def recycle(self):
		self.active = 0
##		self.have_request = 0
##		self.reqdata=[]
		asyncore.dispatcher.close(self)
		self._strmOut = None
		self.server.rhQueue.put(self)
		self.readfile.reset()

	def log(self, message):
		pass

	def handle_error(self, x, y, z):
   		t, v, tbinfo = sys.exc_info()
	   	if t == exceptions.KeyboardInterrupt:
	   		self.server.shutDown()
	   	else:
			if debug:
				print "Error caught in asyncore."
				print "The type is %s, %s" % (t,v)
				import traceback
				traceback.print_tb(tbinfo)

class Monitor(asyncore.dispatcher):
	"""
	This is a dispatch class that handles requests on the monitor port.
	"""

	def __init__(self, server):
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		addr = ((server.address()[0],server.address()[1]-1))
		self.addr = addr
		self.bind(addr)
		self.listen(5)
		self.server = server
		print "Monitor socket connected"

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
		rh.activate(conn, self.addr)

	def log(self, message):
		pass




def run(useMonitor=0):
	from errno import EINTR
	import select
	global server
	global monitor
	try:
		server = None
		try:
			server = AsyncThreadedAppServer()
		except Exception, e:
			print "Error starting the AppServer"
			tb = sys.exc_info()
			print "Traceback:\n"
			print tb[0]
			print tb[1]
			import traceback
			traceback.print_tb(tb[2])
			sys.exit()

		if useMonitor:
			monitor = 1
			monitor_socket = Monitor(server)
		else:
			monitor = 0

		try:
			asyncore.loop(2)
		except select.error, v:
			if v[0] == EINTR:
				print "Shutdown not completely clean"
			elif v[0] == 0: pass
			else: raise
		except KeyboardInterrupt, e:
			print "Initiating Shutdown"
		except Exception, e:
			print e
			print "Error, Exiting AppServer"
			if 1: #See the traceback from an exception
				tb = sys.exc_info()
				print "Traceback:\n"
				print tb[0]
				print tb[1]
				import traceback
			traceback.print_tb(tb[2])
	finally:
		if server:
			if server.running:
				server.initiateShutdown()
			server._closeThread.join()
	#sys.exit()


def shutDown(arg1,arg2):
	global server
	print "Shutdown Called"
	server.initiateShutdown()

import signal
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)


usage = """
The AppServer is the main process of WebKit.  It handles requests for servlets from webservers.
AsyncThreadedAppServer takes the following command line arguments:
stop:  Stop the currently running Apperver.
daemon: run as a daemon
If AppServer is called with no arguments, it will start the AppServer and record the pid of the process in appserverpid.txt
"""


def main(args=[]):
	monitor=0
	function=run
	daemon=0
	for i in args:
		if i == "monitor":
			print "Enabling Monitoring"
			monitor=1
		elif i == "stop":
			import AppServer
			function=AppServer.stop
		elif i == "daemon":
			daemon=1
		elif i == "start":
			pass
		else:
			print usage

	if 0: #this doesn't work
		import profile
		profile.run(run(), "profile.txt")
	else:
		if daemon:
			if os.name == "posix":
				pid=os.fork()
				if pid:
					sys.exit()
			else:
				print "daemon mode not available on your OS"
		function(monitor)

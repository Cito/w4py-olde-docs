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
from MiscUtils.Funcs import timestamp
from marshal import dumps, loads
import os, sys
from threading import Lock, Thread, Event
import threading
import Queue
import select
import socket
import threading
import time
import errno
import traceback
from WebUtils import Funcs

debug = 0

DefaultConfig = {
	'Port':                 8086,
	'MaxServerThreads':        20,
	'MinServerThreads':        5,
	'StartServerThreads':      10,

	# @@ 2000-04-27 ce: None of the following settings are implemented
#	'RequestQueueSize':     16,#	'RequestBufferSize':    64*1024,
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

	def __init__(self, path=None):
		AppServer.__init__(self, path)
		self._addr = None
		threadCount = self.setting('StartServerThreads')
		self.maxServerThreads = self.setting('MaxServerThreads')
		self.minServerThreads = self.setting('MinServerThreads')
		self.monitorPort = None
		self.threadPool = []
		self.threadCount=0
		self.threadUseCounter=[]
		self.requestQueue = Queue.Queue(self.maxServerThreads * 2) # twice the number of threads we have
		self.rhQueue = Queue.Queue(0) # This will grow to a limit of the number of
		                              # threads plus the size of the requestQueue plus one.
		                              # But it's easier to just let it be unlimited.

		self.mainsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# Must use SO_REUSEADDR to avoid problems restarting the app server
		# This was discussed on Webware-devel in Oct 2001, and this solution
		# was found by Jeff Johnson
		self.mainsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		addr = self.address()
		try:
			self.mainsocket.bind(addr)
		except:
			if self.running:
				self.initiateShutdown()
			self._closeThread.join()
			raise
		print "Listening on", addr
		open(self.serverSidePath('address.text'), 'w').write('%s:%d' % (addr[0], addr[1]))
		self.monitorPort = addr[1]-1

		out = sys.stdout

		out.write('Creating %d threads' % threadCount)
		for i in range(threadCount):
			self.spawnThread()
			out.write(".")
			out.flush()
		out.write("\n")

		# @@ 2001-05-30 ce: another hard coded number:  @@jsl- not everything needs to be configurable....
		self.mainsocket.listen(1024)
		self.recordPID()

		print "Ready\n"

	def isPersistent(self):
		return 1

	def mainloop(self, monitor=None, timeout=1):
		from errno import EINTR

		inputsockets = [self.mainsocket,]
		if monitor:
			inputsockets.append(monitor.insock)

		threadCheckInterval = 100  #does this need to be configurable???
		threadUpdateDivisor = 10 #grabstat interval
		threadCheck=0

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
						rh = self.rhQueue.get_nowait()
					except Queue.Empty:
						rh = RequestHandler(self)
					rh.activate(client, self._reqCount)
					self.requestQueue.put(rh)

			if threadCheck % threadUpdateDivisor == 0:
				self.updateThreadUsage()

			if threadCheck > threadCheckInterval:
				if debug: print "Busy Threads: ", self.activeThreadCount()
				threadCheck=0
				self.manageThreadCount()
			else: threadCheck = threadCheck+1

	def activeThreadCount(self):
		"""
		Get a snapshot of the number of threads currently in use.
		"""
		count=0
		for i in self.threadPool:
			if i.processing: count = count+1
		return count


	def updateThreadUsage(self):
		"""
		Update the threadUseCounter list.
		"""
		count = self.activeThreadCount()
		if len(self.threadUseCounter) > 10:
			self.threadUseCounter.pop(0)
		self.threadUseCounter.append(count)


	def manageThreadCount(self):
		"""
		Adjust the number of threads in use.
		This algorithm needs work.  The edges (ie at the minserverthreads) are tricky.
		When working with this, remember thread creation is CHEAP
		"""

		avg=0
		max=0

		for i in self.threadUseCounter:
			avg = avg + i
			if i > max:
				max = i
		avg = avg / len(self.threadUseCounter)
		if debug: print "Average Thread Use: ", avg
		if debug: print "Max Thread Use: ", max
		if debug: print "ThreadCount: ", self.threadCount

		if avg==0: return #we have no observations to use

		margin = self.threadCount / 4 #smoothing factor
		if debug: print "margin=", margin

		if avg == self.threadCount and self.threadCount < self.maxServerThreads:
			self.spawnThread()
		elif avg < self.threadCount - margin and self.threadCount > self.minServerThreads:
			self.absorbThread()

	def spawnThread(self):
		if debug: print "Spawning new thread"
		t = Thread(target=self.threadloop)
		t.processing=0
		t.start()
		self.threadPool.append(t)
		self.threadCount = self.threadCount+1
		if debug: print "New Thread Spawned, threadCount=", self.threadCount
		self.threadUseCounter=[] #reset

	def absorbThread(self):
		if debug: print "Absorbing Thread"
		self.requestQueue.put(None)
		self.threadCount = self.threadCount-1
		for i in self.threadPool:
			if not i.isAlive():
				rv=i.join() #Don't need a timeout, it isn't alive
				self.threadPool.remove(i)
				if debug: print "Thread Absorbed, threadCount=", self.threadCount
		self.threadUseCounter=[]

	def threadloop(self):
		self.initThread()

		t=threading.currentThread()
		t.processing=0
		try:
			while 1:
				try:
					rh=self.requestQueue.get()
					if rh == None: #None means time to quit
						if debug: print "Thread retrieved None, quitting"
						break
					if self.running:
						t.processing=1
						try:
							rh.handleRequest()
						except:
							traceback.print_exc(file=sys.stderr)
						t.processing=0
					rh.close()
				except Queue.Empty:
					pass
		finally:
			self.delThread()
		if debug: print threading.currentThread(), "Quitting"

	def initThread(self):
		''' Invoked immediately by threadloop() as a hook for subclasses. This implementation does nothing and subclasses need not invoke super. '''
		pass

	def delThread(self):
		''' Invoked immediately by threadloop() as a hook for subclasses. This implementation does nothing and subclasses need not invoke super. '''
		pass

	def awakeSelect(self):
		"""
		Send a connect to ourself to pop the select() call out of it's loop safely
		"""
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		addr = self.address()
		try:
			sock.connect(addr)
			sock.close()
		except:
			pass
		return


	def shutDown(self):
		self.running=0
		self.awakeSelect()
		self._shuttingdown=1  #jsl-is this used anywhere?
		print "ThreadedAppServer: Shutting Down"
		self.mainsocket.close()
		for i in range(self.threadCount):
			self.requestQueue.put(None)#kill all threads
		for i in self.threadPool:
			try:
				i.join()
			except:
				pass
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
		print "******** Listening to Monitor Socket ************"

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

		BUFSIZE = 8*1024


		chunk = ''
		missing = int_length
		while missing > 0:
			block = conn.recv(missing)
			if not block:
				conn.close()
				raise NotEnoughDataError, 'received only %d out of %d bytes when receiving dict_length' % (len(chunk), int_length)
			chunk = chunk + block
			missing = int_length - len(chunk)
		dict_length = loads(chunk)
		if type(dict_length) != type(1):
			conn.close()
			print "Error: Invalid AppServer protocol"
			return 0

		chunk = ''
		missing = dict_length
		while missing > 0:
			block = conn.recv(missing)
			if not block:
				conn.close()
				raise NotEnoughDataError, 'received only %d out of %d bytes when receiving dict' % (len(chunk), dict_length)
			chunk = chunk + block
			missing = dict_length - len(chunk)

		dict = loads(chunk)

		if dict['format'] == "STATUS":
			conn.send(str(self.server._reqCount))

		if dict['format'] == 'QUIT':
			conn.send("OK")
			conn.close()
			self.server.shutDown()



from WebKit.ASStreamOut import ASStreamOut
class TASASStreamOut(ASStreamOut):

	def __init__(self, sock):
		ASStreamOut.__init__(self)
		self._socket = sock

	def flush(self):
		debug=0
		result = ASStreamOut.flush(self)
		if result: ##a true return value means we can send
			reslen = len(self._buffer)
			if debug: print "TASASStreamout is sending %s bytes" % reslen
			sent = 0
			while sent < reslen:
				try:
					sent = sent + self._socket.send(self._buffer[sent:sent+8192])
				except socket.error, e:
					if e[0]==errno.EPIPE: #broken pipe
						pass
					else:
						print "StreamOut Error: ", e
					break
			self.pop(sent)


class RequestHandler:

	def __init__(self, server):
		self.server = server

	def activate(self, sock, number):
		'''
		Activates the handler for processing the request.
		Number is the number of the request, mostly used to identify
		verbose output. Each request should be given a unique,
		incremental number.
		'''
		self.sock = sock
#		self._strmOut = TASASStreamOut(sock)
		self._number = number

	def close(self):
		self.sock = None
#		self._strmOut = None
		self.server.rhQueue.put(self)

	def handleRequest(self):

		verbose = self.server._verbose

		startTime = time.time()
		if verbose:
			print '%5i  %s ' % (self._number, timestamp()['pretty']),

		conn = self.sock

		# @@ 2001-05-30 ce: Ack! Look at this hard coding.
		BUFSIZE = 8*1024

		data = []

		chunk = ''
		missing = int_length
		while missing > 0:
			block = conn.recv(missing)
			if not block:
				conn.close()
				raise NotEnoughDataError, 'received only %d out of %d bytes when receiving dict_length' % (len(chunk), int_length)
			chunk = chunk + block
			missing = int_length - len(chunk)
		dict_length = loads(chunk)
		if type(dict_length) != type(1):
			conn.close()
			print
			print "Error: Invalid AppServer protocol"
			return 0

		chunk = ''
		missing = dict_length
		while missing > 0:
			block = conn.recv(missing)
			if not block:
				conn.close()
				raise NotEnoughDataError, 'received only %d out of %d bytes when receiving dict' % (len(chunk), dict_length)
			chunk = chunk + block
			missing = dict_length - len(chunk)

		dict = loads(chunk)
		#if verbose: print "Comm Delay=%s" % (time.time() - dict['time'])

		if dict:
			if verbose:
				if dict.has_key('environ'):
					requestURI = Funcs.requestURI(dict['environ'])
				else:
					requestURI = None
				print requestURI

		dict['input'] = conn.makefile("rb",8012)

		strmOut = TASASStreamOut(self.sock)
		transaction = self.server._app.dispatchRawRequest(dict, strmOut)
		strmOut.close()


		try:
			conn.shutdown(1)
			conn.close()
		except:
			pass

		if verbose:
			duration = '%0.2f secs' % (time.time() - startTime)
			duration = string.ljust(duration, 19)
			print '%5i  %s  %s' % (self._number, duration, requestURI)
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

# This will be thrown when less data arrived on the socket than we were expecting.
class NotEnoughDataError(Exception):
	pass


def run(useMonitor = 0, workDir=None):
	global server
	global monitor
	monitor = useMonitor
	try:
		server = None
		server = ThreadedAppServer(workDir)
		if useMonitor:
			monitor_socket = Monitor(server)
		else:
			monitor_socket = None

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
				server.mainloop(monitor_socket)
			except KeyboardInterrupt, e:
				server.shutDown()
	except Exception, e:
		if not isinstance(e, SystemExit):
			import traceback
			traceback.print_exc(file=sys.stderr)
		#print e
		print
		print "Exiting AppServer"
		if server:
			if server.running:
				server.initiateShutdown()
			server._closeThread.join()
	sys.exit()


def shutDown(arg1,arg2):
	global server
	print "Shutdown Called"
	if server:
		server.initiateShutdown()
	else:
		print 'WARNING: No server reference to shutdown.'

import signal
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)




usage = """
The AppServer is the main process of WebKit.  It handles requests for servlets from webservers.
ThreadedAppServer takes the following command line arguments:
stop:  Stop the currently running Apperver.
daemon: run as a daemon
If AppServer is called with no arguments, it will start the AppServer and record the pid of the process in appserverpid.txt
"""


def main(args):
	monitor=0
	function=run
	daemon=0
	workDir=None

	for i in args[:]:
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
		elif i[:8] == "workdir=":
			workDir = i[8:]
		else:
			print usage

	if 0:
		import profile
		profile.run("main()", "profile.txt")
	else:
		if daemon:
			if os.name == "posix":
				pid=os.fork()
				if pid:
					sys.exit()
			else:
				print "daemon mode not available on your OS"
		function(monitor, workDir)

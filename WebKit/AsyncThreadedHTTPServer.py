#!/usr/bin/env python
"""
********************************************************************************
WARNING:  This is not a full webserver.  It supports only GET and POST requests.
********************************************************************************

This is an EXPERIMENTAL web server version of WebKit.  It
serves http directly, without needing to be run in conjunction with
an external web server.  As a result, it should be very fast.  It
could be used with Apache acting as a proxy for SSL and to serve
static files.  It could also be useful in situations where you need
dynamic web capability but you don't want or need to install a
full web server.  You could, for example, embed this web server into
another product to expose some web reporting and control
capabilities and perhaps some XML-RPC functionality, and save
yourself the headache of having to install and configure
Apache or another web server to run along with your product.

I repeat, this is EXPERIMENTAL.  If you try it out, please
let us know how it works by dropping an email to the Webware discussion
list at webware-discuss@lists.sourceforge.net

To use this, you'll have to get your web browser to connect to
the port specified in AppServer.config, which defaults to
port 8086.  Use a url like http://localhost:8086/Examples/ to
try this out.  You can also modify the 8086 to 80 in AppServer.config
if you want this to serve on the default port for web servers.

To-Do:
    - Comment the code in HTTPRequestHandler.
"""

if __name__=='__main__':
	import sys
	print 'To run this server, try this instead:'
	print 'python Launch.py AsyncThreadedHTTPServer'
	sys.exit(1)


from AsyncThreadedAppServer import Monitor, MainRelease
import AsyncThreadedAppServer

from cStringIO import StringIO
import urllib, string, time, asyncore, socket
import sys, os
from threading import RLock
import mimetools

global monitor
monitor=0

debug=0

class AsyncThreadedHTTPServer2(AsyncThreadedAppServer.AsyncThreadedAppServer):
	"""
	This derived class customizes AsyncThreadedAppServer so that it
	can serve HTTP requests directly, using a different implementation
	of RequestHandler from the one defined in AsyncThreadedAppServer.py.
	See below for the modified version of RequestHandler.
	"""
	def __init__(self, path=None):
		AsyncThreadedAppServer.AsyncThreadedAppServer.__init__(self, path)
		# Use a custom request handler class that is designed to respond
		# to http directly
		self.setRequestHandlerClass(HTTPRequestHandler)
		self._serverName = None

	def serverName(self):
		host, port = self.socket.getsockname()
		if not host or host == '0.0.0.0':
			host = socket.gethostname()
		hostname, hostnames, hostaddrs = socket.gethostbyaddr(host)
		if '.' not in hostname:
			for host in hostnames:
				if '.' in host:
					hostname = host
					break
		self.server_name = hostname
		self.server_port = port
		self._serverName = hostname
		return hostname



	def serverPort(self):
		'''
		Returns the server port.
		'''
		return self.address()[1]


from WebKit.ASStreamOut import ASStreamOut
class ASTHSStreamOut(ASStreamOut):
	"""
	This class handles a response stream for AsyncThreadedAppServer.
	"""
	def __init__(self, trigger):
		ASStreamOut.__init__(self)
		self._lock = RLock() #we need an reentrant lock because the write method uses the lock, but it can also call flush, which also uses the lock
		self._trigger = trigger

	def close(self):
		ASStreamOut.close(self)
		self._trigger.release()

	def writeable(self):
		"""
		Called by asyncore to ask if we want to write data
		"""
		if debug: print "writeable called with self._comm=%s and len(buffer)=%s"%(self._committed, len(self._buffer))
		if self._closed: return 1
		return self._committed and len(self._buffer)

	def flush(self):
		if debug: print "ASTASStreamOut Flushing"
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



class HTTPRequestHandler(asyncore.dispatcher):
	"""
	Has the methods that process the request.

	An instance of this class is activated by AsyncThreadedHTTPServer.
	When activated, it is listening for the request to come in.  asyncore will
	call handle_read when there is data to be read.  Once all the request has
	been read, it will put itself in the requestQueue to be picked up by a
	thread and processed by calling handleRequest. Once the processing is
	complete, the thread drops the instance and tries to find another one.
	This instance notifies asyncore that it is ready to send.
	"""


	def __init__(self, server):
		self.server=server
		self.have_request = 0
		self.have_response = 0
		self.reqdata=''
		self.request_data=[]
		self._buffer = ''
		self.haveheader=0
		self.reqtype=''

	def handleRequest(self):
		#check for status message
		if self.reqdata == "STATUS":
			self._buffer = str(self.server._reqCount)
			self.have_response = 1
			return

		verbose = self.server._verbose

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
		self.rfile = StringIO(self.reqdata[string.find(self.reqdata,"\n")+1:])
		self.headers = mimetools.Message(self.rfile)
		self.handleHTTPRequest()

		self.have_response = 1

		if verbose:
			print 'connection closed.'
			print '%0.2f secs' % (time.time() - startTime)
			print 'END REQUEST'
			print

		if hasattr(self, 'transaction'):
			self.transaction._application=None
			self.transaction.die()
			del self.transaction
		MainRelease.release()

	def activate(self, sock, addr):
		self.set_socket(sock)
		self.clientf = sock.makefile("r+",0)
		self.active = 1
		self.client_address = addr
		self._strmOut = ASTHSStreamOut(MainRelease)
		self.statusSent=0

	def readable(self):
		return self.active and not self.have_request

	def writable(self):
		"""
		Always ready to write, otherwise we might have to wait for a timeout to be asked again
		"""
		return self.active and self._strmOut.writeable()

	def handle_connect(self):
		pass

	def handle_read(self):
		if not self.haveheader:
			data = string.strip(self.clientf.readline())
			if data:
				self.request_data.append(data+"\r\n")
				return
			self.haveheader = 1
			self.request_data.append("\r\n")
			try:
				self.reqtype = string.split(self.request_data[0])[0]
			except:
				self.close()
			if string.lower(self.reqtype) == "get":
				self.reqdata = string.join(self.request_data,"")
				self.have_request = 1
				self.path = string.split(self.request_data[0])[1]
				self.server.requestQueue.put(self)
			elif string.lower(self.reqtype) == "post":
				for i in self.request_data:
					if string.lower(string.split(i,":")[0]) =="content-length":
						self.datalength = int(string.split(i)[1])
						break
				self.path = string.split(self.request_data[0])[1]
				self.reqdata=string.join(self.request_data,"")
				self.request_data = []
		else:
			data = self.recv(self.datalength)
			self.request_data.append(data)
			self.datalength = self.datalength - len(data)
			if self.datalength > 0:
				return
			self.inputdata = string.join(self.request_data,"")
			self.have_request = 1
			self.server.requestQueue.put(self)


	def handle_write(self):
		if not self.statusSent:
			if string.lower(self._strmOut._buffer[:7]) == "status:" :
				self._strmOut._buffer = "HTTP/1.0 " + self._strmOut._buffer[8:]
			else:
				self._strmOut._buffer = "HTTP/1.0 200 OK\r\n" + self._strmOut._buffer
			self.statusSent=1
		try:
			sent = self.send(self._strmOut._buffer)
		except socket.error, e:
			if e[0] == 32: #bad file descriptor
				self.close()
				return
		self._strmOut.pop(sent)

		 #if the servlet has returned and there is no more data in the buffer
		if self._strmOut.closed() and len(self._strmOut._buffer)==0:
			self.socket.shutdown(1)
			self.close()
			#For testing
		elif len(self._strmOut._buffer) > 0:
			MainRelease.release() #let's send the rest
		if debug:
			sys.stdout.write(".")
			sys.stdout.flush()



	def close(self):
		self.clientf=None
		try:
			self.shutdown(1)
		except:
			pass
		try:
			asyncore.dispatcher.close(self)
		except:
			pass
		self.active = 0
		self.have_request = 0
		self.have_header = 0
		self.reqtype=''
		self.reqdata=''
		self.request_data=[]
		self.haveheader=0
		self.datalength=0
		self._strmOut = None
		self.server.rhQueue.put(self)

	def log(self, message):
		pass

	def do_POST(self):
		self.handleHTTPRequest()

	def do_GET(self):
		self.handleHTTPRequest()

	def handleHTTPRequest(self):
		path = self.path
		i = string.rfind(path, '?')
		if i >= 0:
			path, query = path[:i], path[i+1:]
		else:
			query = ''

		env = {}
		env['SERVER_SOFTWARE'] = "WebKit.HTTPServer" ##self.version_string()
		env['GATEWAY_INTERFACE'] = 'CGI/1.1'
		env['SERVER_PROTOCOL'] = "HTTP/1.0" ##self.protocol_version
		env['SERVER_NAME'] = self.server.serverName()
		env['HTTP_HOST'] = self.server.serverName()
		env['SERVER_PORT'] = str(self.server.serverPort())
		env['REQUEST_METHOD'] = self.reqtype
		uqrest = urllib.unquote(path)
		env['PATH_INFO'] = uqrest
		#env['PATH_TRANSLATED'] = self.translate_path(uqrest)
		env['SCRIPT_NAME'] = ''
		env['QUERY_STRING'] = query
		host, port = self.client_address
		#host = self.address_string()
		#if host != self.client_address[0]:
		#    env['REMOTE_HOST'] = host
		env['REMOTE_HOST'] = host
                env['REMOTE_ADDR'] = host
		env['REMOTE_PORT'] = str(port)
#		print 'REMOTE_PORT = %d' % port
		# AUTH_TYPE
		# REMOTE_USER
		# REMOTE_IDENT
		if self.headers.typeheader is None:
			env['CONTENT_TYPE'] = self.headers.type
		else:
			env['CONTENT_TYPE'] = self.headers.typeheader
		length = self.headers.getheader('Content-Length')
		if length:
			#print "*******Length=",length
			env['CONTENT_LENGTH'] = length
			input = self.inputdata
		else:
			input = ''
		for name, value in self.headers.items():
			env['HTTP_' + string.upper(string.replace(name, '-', '_'))] = value

		dict = {
				'format': 'CGI',
				'time':   time.time(),
				'environ': env,
				'input':   StringIO(input)
				}

		self.transaction = self.server._app.dispatchRawRequest(dict, self._strmOut)
		self._strmOut.close()



	def log_message(self, format, *args):
		if debug:
			BaseHTTPServer.log_message(self, format, args)






def run(useMonitor=0, workDir=None):
	from errno import EINTR
	import select
	global server
	global monitor
	try:
		server = None
		try:
			server = AsyncThreadedHTTPServer2(workDir)
			print __doc__
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
	sys.exit()


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


def main(args):
	monitor=0
	function=run
	daemon=0
	workDir=None

	for i in args:
		if i == "monitor":
			print "Enabling Monitoring"
			monitor=1
		elif i == "stop":
			import AppServer
			function=AppServer.stop
		elif i == "daemon":
			daemon=1
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

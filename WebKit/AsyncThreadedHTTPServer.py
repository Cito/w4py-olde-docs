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
    - The HTTPRequestHandler class inherits from the standard Python library's
      BaseHTTPRequestHandler class but uses it in a different way from how
      it was intended to be used.  It might be less confusing, and more
      maintainable if we copied the code we're using from
      BaseHTTPRequestHandler into RequestHandler itself.  (Usually
      cut-and-paste isn't the best way to reuse code, but in this case it's
      probably preferable because of the unusual way we're using
      BaseHTTPRequestHandler.)
    
    - Comment the code in HTTPRequestHandler.      
"""

from AsyncThreadedAppServer import Monitor, MainRelease
import AsyncThreadedAppServer

from cStringIO import StringIO
from BaseHTTPServer import BaseHTTPRequestHandler
import urllib, string, time, asyncore, socket
import sys, os

global monitor
monitor=0

debug=0

class AsyncThreadedHTTPServer(AsyncThreadedAppServer.AsyncThreadedAppServer):
	'''
	This derived class customizes AsyncThreadedAppServer so that it
	can serve HTTP requests directly, using a different implementation
	of RequestHandler from the one defined in AsyncThreadedAppServer.py.
	See below for the modified version of RequestHandler.
	'''
	def __init__(self):
		AsyncThreadedAppServer.AsyncThreadedAppServer.__init__(self)
		# Use a custom request handler class that is designed to respond
		# to http directly
		self.setRequestHandlerClass(HTTPRequestHandler)
		self._serverName = None		
	
	def serverName(self):
		'''
		Returns the server name.
		'''
		# I didn't write this code myself, but I can't remember where I got it
		# from.  In any case, it seems to do what we need.
		return 'localhost'
		if self._serverName is None:
			host, port = self.address()
			print "Using hostname %s" % host
			if not host or host == '0.0.0.0':
				host = socket.gethostname()

			hostname, hostnames, hostaddrs = socket.gethostbyaddr(host)
			if '.' not in hostname:
				for host in hostnames:
					if '.' in host:
						hostname = host
						break
			self._serverName = hostname
		return self._serverName

	def serverPort(self):
		'''
		Returns the server port.
		'''
		return self.address()[1]



class HTTPRequestHandler(asyncore.dispatcher, BaseHTTPRequestHandler):
	"""
	Has the methods that process the request.  This class inherits from
	BaseHTTPRequestHandler but uses it in a somewhat strange way.  It would
	probably be better to eliminate BaseHTTPRequestHandler as a base class
	and instead simply move the necessary code into this class.
	
	An instance of this class is activated by AsyncThreadedHTTPServer.
	When activated, it is listening for the request to come in.  asyncore will
	call handle_read when there is data to be read.  ONce all the request has
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
		self.rfile = StringIO(self.reqdata)
		self.wfile = StringIO()
		self.handle()

		self._buffer = self.wfile.getvalue()
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
		self._buffer=''
		self.active = 1
		self.client_address = addr
		
	def readable(self):
		return self.active and not self.have_request

	def writable(self):
		"""
		Always ready to write, otherwise we might have to wait for a timeout to be asked again
		"""
		return self.have_response

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
				self.server.requestQueue.put(self)
			elif string.lower(self.reqtype) == "post":
				for i in self.request_data:
					if string.lower(string.split(i,":")[0]) =="content-length":
						self.datalength = int(string.split(i)[1]) + 2
		else:
			data = self.recv(self.datalength)
			self.request_data.append(data)
			self.datalength = self.datalength - len(data)
			if self.datalength > 0:
				return
			self.reqdata = string.join(self.request_data,"")
			self.have_request = 1
			self.server.requestQueue.put(self)

			


	def handle_write(self):
		if not self.have_response: return
		sent = self.send(self._buffer)
		self._buffer = self._buffer[sent:]
		if len(self._buffer) == 0:
			self.close()
		else:
			MainRelease.release()
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
		self.have_response = 0
		self.have_header = 0
		self.reqtype=''
		self.reqdata=''
		self.request_data=[]
		self.haveheader=0
		self.datalength=0
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
		env['SERVER_SOFTWARE'] = self.version_string()
		env['GATEWAY_INTERFACE'] = 'CGI/1.1'
		env['SERVER_PROTOCOL'] = self.protocol_version
		env['SERVER_NAME'] = self.server.serverName()
		env['HTTP_HOST'] = self.server.serverName()
		env['SERVER_PORT'] = str(self.server.serverPort())
		env['REQUEST_METHOD'] = self.command
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
		env['REMOTE_PORT'] = str(port)
#		print 'REMOTE_PORT = %d' % port
		# AUTH_TYPE
		# REMOTE_USER
		# REMOTE_IDENT
		if self.headers.typeheader is None:
			env['CONTENT_TYPE'] = self.headers.type
		else:
			env['CONTENT_TYPE'] = self.headers.typeheader
		length = self.headers.getheader('content-length')
		if length:
			env['CONTENT_LENGTH'] = length
#			print 'reading %d chars of input' % int(length)
			input = self.rfile.read(int(length))
#			print 'done reading; input is %d chars long' % int(len(input))
		else:
			input = ''
		for name, value in self.headers.items():
			env['HTTP_' + string.upper(string.replace(name, '-', '_'))] = value

		dict = {
				'format': 'CGI',
				'time':   time.time(),
				'environ': env,
				'input':   input
				}

		self.transaction = self.server._app.dispatchRawRequest(dict)
		
		response = self.transaction.response()
		self.send_response(response.header('Status', 200))
		rawResponse = response.rawResponse()
		for keyword, value in rawResponse['headers']:
			self.send_header(keyword, value)
		self.end_headers()
		self.wfile.write(rawResponse['contents'])

	def log_message(self, format, *args):
		if debug:
			BaseHTTPServer.log_message(self, format, args)






def run(useMonitor=0):
	from errno import EINTR
	import select
	global server
	global monitor
	try:
		server = None
		try:
			server = AsyncThreadedHTTPServer()
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
##	if len(args)>1:
	monitor=0
	function=run
	daemon=0
	
	for i in args[1:]:
		if i == "monitor":
			print "Enabling Monitoring"
			monitor=1
		elif i == "stop":
			import AppServer
			function=AppServer.stop
		elif i == "daemon":
			daemon=1
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
		function(monitor)

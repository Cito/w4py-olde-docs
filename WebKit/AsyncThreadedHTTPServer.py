#!/usr/bin/env python
"""
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
    
    - Perform additional testing.  It has been very lightly tested with Python
      1.5.2 and 2.0 on Windows NT 4.0 only.  It ought to work on other
      platforms without modification but hasn't yet been tested.

    - Comment the code in HTTPRequestHandler.      
"""

from AsyncThreadedAppServer import AsyncThreadedAppServer, Monitor, MainRelease

from cStringIO import StringIO
from BaseHTTPServer import BaseHTTPRequestHandler
import urllib, string, time, asyncore, socket


class AsyncThreadedHTTPServer(AsyncThreadedAppServer):
	'''
	This derived class customizes AsyncThreadedAppServer so that it
	can serve HTTP requests directly, using a different implementation
	of RequestHandler from the one defined in AsyncThreadedAppServer.py.
	See below for the modified version of RequestHandler.
	'''
	def __init__(self):
		AsyncThreadedAppServer.__init__(self)
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
		if self._serverName is None:
			host, port = self.address()
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
		self.reqdata=[]
		self._buffer = ''

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
		self._buffer=''
		self.active = 1
		self.client_address = addr
		
	def readable(self):
		return self.active and not self.have_request

	def writable(self):
		"""
		Always ready to write, otherwise we might have to wait for a timeout to be asked again
		"""
		#return self.active
		return self.have_response

	def handle_connect(self):
		pass

	def handle_read(self):
		data = self.recv(8192)
		if len(data) == 8192:
			self.reqdata.append(data)
		else:
			self.reqdata.append(data)
			self.reqdata = string.join(self.reqdata,'')
			self.have_request=1
			self.server.requestQueue.put(self)
			#self.socket.shutdown(0)

	def handle_write(self):
		if not self.have_response: return
		sent = self.send(self._buffer)
		self._buffer = self._buffer[sent:]
		if len(self._buffer) == 0:
			self.close()
			#For testing
		if __debug__:
			sys.stdout.write(".")
			sys.stdout.flush()

	def close(self):
		self.active = 0
		self.have_request = 0
		self.have_response = 0
		self.reqdata=[]
		asyncore.dispatcher.close(self)
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
		print 'REMOTE_PORT = %d' % port
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
			print 'reading %d chars of input' % int(length)
			input = self.rfile.read(int(length))
			print 'done reading; input is %d chars long' % int(len(input))
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


def main(monitor = 0):
	try:
		server = None
		server = AsyncThreadedHTTPServer()
		if monitor:
			monitor = Monitor(server)
		asyncore.loop()
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

import BaseHTTPServer, mimetools
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO
import threading, socket
from WebKit.ThreadedAppServer import Handler
from WebKit.ASStreamOut import ASStreamOut
from os import getenv
import time
import errno

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	"""Handles incoming requests.

	Recreated with every request. Abstract base class.

	"""

	# This sends the common CGI variables, except the following:
	# HTTP_CONNECTION, HTTP_KEEP_ALIVE
	# DOCUMENT_ROOT, PATH_TRANSLATED, SCRIPT_FILENAME
	# SERVER_NAME, SERVER_ADMIN, SERVER_SIGNATURE

	def handleRequest(self):
		"""Handle a request.

		Actually performs the request, creating the environment and calling
		self.doTransaction(env, myInput) to perform the response.

		"""
		self.server_version = 'Webware/' + self._server.version()
		env = {}
		if self.headers.has_key('Content-Type'):
			env['CONTENT_TYPE'] = self.headers['Content-Type']
			del self.headers['Content-Type']
		key = 'If-Modified-Since'
		if self.headers.has_key(key):
			env[key] = self.headers[key]
			del self.headers[key]
		self.headersToEnviron(self.headers, env)
		env['REMOTE_ADDR'], env['REMOTE_PORT'] = map(str, self.client_address)
		env['REQUEST_METHOD'] = self.command
		path = self.path
		if path.find('?') != -1:
			env['REQUEST_URI'], env['QUERY_STRING'] = path.split('?', 1)
		else:
			env['REQUEST_URI'] = path
			env['QUERY_STRING'] = ''
			env['SCRIPT_NAME'] = ''
		env['PATH'] = getenv('PATH', '')
		env['PATH_INFO'] = env['REQUEST_URI']
		env['SERVER_ADDR'], env['SERVER_PORT'] = map(str, self._serverAddress)
		env['SERVER_SOFTWARE'] = self.server_version
		env['SERVER_PROTOCOL'] = self.protocol_version
		env['GATEWAY_INTERFACE'] = 'CGI/1.1'
		myInput = ''
		if self.headers.has_key('Content-Length'):
			myInput = self.rfile.read(int(self.headers['Content-Length']))
		self.doTransaction(env, myInput)

	do_GET = do_POST = do_HEAD = handleRequest
	# These methods are used in WebDAV requests:
	do_OPTIONS = do_PUT = do_DELETE = handleRequest
	do_MKCOL = do_COPY = do_MOVE = handleRequest
	do_PROPFIND = handleRequest

	def headersToEnviron(self, headers, env):
		"""Convert headers to environment variables.

		Use a simple heuristic to convert all the headers to
		environmental variables.

		"""
		for header, value in headers.items():
			env['HTTP_%s' % (header.upper().replace('-', '_'))] = value
		return env

	def processResponse(self, data):
		"""Process response.

		Takes a string (like what a CGI script would print) and
		sends the actual HTTP response (response code, headers, body).

		"""
		s = StringIO(data)
		headers = mimetools.Message(s)
		self.doLocation(headers)
		self.sendStatus(headers)
		self.sendHeaders(headers)
		self.sendBody(s)

	def doLocation(self, headers):
		"""Process location header.

		If there's a Location header and no Status header,
		we need to add a Status header ourselves.

		"""
		if headers.has_key('Location'):
			if not headers.has_key('Status'):
				# @@ is this the right status header?
				headers['Status'] = '301 Moved Permanently'

	def sendStatus(self, headers):
		"""Send status."""
		if not headers.has_key('Status'):
			status = "200 OK"
		else:
			status = headers['Status']
			del headers['Status']
		pos = status.find(' ')
		if pos == -1:
			code = int(status)
			message = ''
		else:
			code = int(status[:pos])
			message = status[pos:].strip()
		self.send_response(code, message)

	def sendHeaders(self, headers):
		"""Send headers."""
		for header, value in headers.items():
			self.send_header(header, value)
		self.end_headers()

	def sendBody(self, bodyFile):
		"""Send body."""
		self.wfile.write(bodyFile.read())
		bodyFile.close()

	def log_request(self, code='-', size='-'):
		"""Log request."""
		# Set LogActivity instead.
		pass


class HTTPAppServerHandler(Handler, HTTPHandler):
	"""AppServer interface.

	Adapters HTTPHandler to fit with ThreadedAppServer's
	model of an adapter.

	"""
	protocolName = 'http'
	settingPrefix = 'HTTP'

	def handleRequest(self):
		"""Handle a request."""
		HTTPHandler.__init__(self, self._sock, self._sock.getpeername(), None)

	def doTransaction(self, env, myInput):
		"""Process transaction."""
		streamOut = ASStreamOut()
		requestDict = {
			'format': 'CGI',
			'time': time.time(),
			'environ': env,
			'input': StringIO(myInput),
			'requestID': self._requestID,
			}
		self.dispatchRawRequest(requestDict, streamOut)
		try:
			self.processResponse(streamOut._buffer)
			self._sock.shutdown(2)
		except socket.error, e:
			if e[0] == errno.EPIPE: # broken pipe
				return
			print "HTTPServer: output error:", e # lame

	def dispatchRawRequest(self, requestDict, streamOut):
		"""Dispatch the request."""
		transaction = self._server._app.dispatchRawRequest(requestDict, streamOut)
		streamOut.close()
		transaction._application = None
		transaction.die()
		del transaction

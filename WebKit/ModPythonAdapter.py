###########################################
# mod_python adapter for WebKit
# 
#
# Contributed by: Dave Wallace
# Modified by Jay Love and Geoff Talvola
#
##########################################

"""
Here's how I set up my Apache conf:

<Location /WK >
   SetHandler python-program
   # add the directory that contains ModPythonAdapter.py
   PythonPath "sys.path+['/path/to/WebKit']"
   PythonHandler ModPythonAdapter
   PythonDebug
   </Location>

Make sure you set WEBWARE_ADDRESS_FILE below and now you can access
your running AppServer with:

http://localhost/WK/Welcome


You may also send all requests with a .psp extension to WebKit by adding these lines, outside
of any location or dircetory.

AddHandler python-program .psp
PythonPath "sys.path+['/path/to/WebKit']"
PythonHandler modpHandler::pspHandler

"""

# Fix the current working directory -- this gets initialized incorrectly
# for some reason when run using mod_python.
import os
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass

from mod_python import apache
import time

from socket import *
import sys
import string

from Adapter import Adapter

debug=0
_adapter = None
bufsize = 32*1024

WEBWARE_ADDRESS_FILE='/path/to/Webware/WebKit/address.text'

class ModPythonAdapter(Adapter):
	def __init__(self, host, port):
		webkitdir = os.path.dirname(WEBWARE_ADDRESS_FILE)
		Adapter.__init__(self, webkitdir)
		self.host = host
		self.port = port
		
	def handler(self, req):
		self.reset(req)
		try:
			# Get input
			myInput = self.input(req)

			# get the apache module to do the grunt work of
			#   building the environment
			env=apache.build_cgi_env(req)

			# Fix up the path			
			if not env.has_key('PATH_INFO'): env['PATH_INFO']=req.path_info

			# Communicate with the app server
			respdict = self.transactWithAppServer(env, myInput, self.host, self.port)

			# Respond back to Apache			
			#self.respond(req, respdict)

		except:
			self.handleException(req)
		return apache.OK


	def pspHandler(self, req):
		self.reset(req)
		try:
			# Get input
			myInput = self.input(req)

			# get the apache module to do the grunt work of
			#   building the environment
			env=apache.build_cgi_env(req)

			# Special environment setup needed for psp handler			
			env['WK_ABSOLUTE']=1

			# Fix up the path			
			if not env.has_key('PATH_INFO'): env['PATH_INFO']=req.path_info

			# Communicate with the app server
			respdict = self.transactWithAppServer(env, myInput, self.host, self.port)

			# Respond back to Apache			
			self.respond(req, respdict)

		except:
			self.handleException(req)
		return apache.OK


	def typehandler(self, req):
		""" Not being used yet.
		Probably never be used, b/c the req.handler field is read only in mod_python.
		"""
		self.reset(req)
		debug=1
		if debug:
			ot = open("/tmp/log2.txt","a")
			ot.write("In Type Handler\n")
			ot.flush()

		if req.filename == None:
			return apache.DECLINED
		fn = req.filename
		if debug:
			ot.write("TH: Filename: %s\n"%fn)
		ext = fn[string.rfind(fn,"."):]
		if debug:
			ot.write("TH: Extension: %s\n"%ext)

		if debug:
			ot.write("Req_Handler = %s\n"%req.handler)
			ot.flush()
			ot.close()

		if ext == ".psp":
			req.handler = "python-program"
			return apache.OK
		else:
			return apache.DECLINED


	def input(self, req):
		myInput = ''
		inp = req.read(bufsize)
		# this looks like bad performance if we don't get it all
		#  in the first buffer
		while inp:
			myInput = myInput + inp
			inp = req.read(bufsize)
		return myInput


	def processResponse(self, data):
		req = self.request()
		if self.doneHeader():
			req.write(data)
			return
		headerData = self.headerData() + data
		self.setHeaderData(headerData)
		headerend = string.find(headerData, "\r\n\r\n")
		if headerend < 0:
			return
		headers = headerData[:headerend]
		for i in string.split(headers, "\r\n"):
			header = string.split(i, ":")
			req.headers_out[header[0]] = header[1]
			if string.lower(header[0]) == 'content-type': req.content_type = header[1]
			if string.lower(header[0]) == 'status': req.status = int(string.split(string.lstrip(header[1]),' ')[0])
		req.send_http_header()
		req.write(headerData[headerend+4:])
		self.setDoneHeader(1)

	def handleException(self, req):
		import traceback

		apache.log_error('WebKit mod_python: Error while responding to request\n')
		apache.log_error('Python exception:\n')
		traceback.print_exc(file=sys.stderr)
		
		output = apply(traceback.format_exception, sys.exc_info())
		output = string.join(output, '')
		output = string.replace(output, '&', '&amp;')
		output = string.replace(output, '<', '&lt;')
		output = string.replace(output, '>', '&gt;')
		req.write('''
<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)


	def reset(self, request):
		self.setDoneHeader(0)
		self.setHeaderData('')
		self.setRequest(request)

	# These methods are non-thread-safe.  On platforms like NT where Apache runs multi-threaded,
	# and the same ModPythonAdapter instance may be called simultaneously for different requests,
	# they need to replaced with threadsafe versions.  See WinModPythonAdapter below.
	def doneHeader(self):
		return self._doneHeader
	def setDoneHeader(self, doneHeader):
		self._doneHeader = doneHeader
	def headerData(self):
		return self._headerData
	def setHeaderData(self, headerData):
		self._headerData = headerData
	def request(self):
		return self._request
	def setRequest(self, request):
		self._request = request


# NT-specific, thread-safe version of ModPythonAdapter.  Requires Win32 extensions.
if os.name == 'nt':
	import win32api

	# This is a Windows-specific thread-safe version of ModPythonAdapter.  It replaces the
	# non-thread-safe [set]doneHeader, [set]headerData, and [set]request with versions
	# that store the information keyed by thread ID.
	#
	# This seems a bit hokey, but it was easy to write and it works.
	OriginalModPythonAdapter = ModPythonAdapter
	class WinModPythonAdapter(OriginalModPythonAdapter):
		def __init__(self, host, port):
			OriginalModPythonAdapter.__init__(self, host, port)
			self._threadSafeStorage = {}

		def threadSafeValue(self, name):
			threadID = win32api.GetCurrentThreadId()
			return self._threadSafeStorage[threadID, name]
		def setThreadSafeValue(self, name, value):
			threadID = win32api.GetCurrentThreadId()
			self._threadSafeStorage[threadID, name] = value
		
		def doneHeader(self):
			return self.threadSafeValue('doneHeader')
		def setDoneHeader(self, doneHeader):
			self.setThreadSafeValue('doneHeader', doneHeader)
		def headerData(self):
			return self.threadSafeValue('headerData')
		def setHeaderData(self, headerData):
			self.setThreadSafeValue('headerData', headerData)
		def request(self):
			return self.threadSafeValue('request')
		def setRequest(self, request):
			self.setThreadSafeValue('request', request)
		
	# Replace ModPythonAdapter with the Windows-safe version.
	ModPythonAdapter = WinModPythonAdapter


if _adapter is None:
	(host, port) = string.split(open(WEBWARE_ADDRESS_FILE).read(), ':')
	port = int(port)
	_adapter = ModPythonAdapter(host, port)


def handler(req):
	return _adapter.handler(req)
def pspHandler(req):
	return _adapter.pspHandler(req)
def typehandler(req):
	return _adapter.typehandler(req)

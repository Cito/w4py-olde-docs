import os, sys, time, socket
from marshal import dumps, loads
from Object import Object
from MiscUtils.Configurable import Configurable
import struct, errno

class Adapter(Configurable, Object):

	def __init__(self, webKitDir):
		Configurable.__init__(self)
		Object.__init__(self)
		self._webKitDir = webKitDir
		self._respData = ''

	def name(self):
		return self.__class__.__name__

	def defaultConfig(self):
		return {
			'NumRetries':            20,
			'SecondsBetweenRetries': 3
		}

	def configFilename(self):
		return os.path.join(self._webKitDir, 'Configs/%s.config' % self.name())

	def transactWithAppServer(self, env, myInput, host, port):
		'''Used by subclasses that are communicating with a separate app server via socket.  Returns the unmarshaled response dictionary.'''
		dict = {
				'format': 'CGI',
				'time':   time.time(),
				'environ': env,
				}

		retries = 0
		while 1:

			try:
				# Send our request to the AppServer
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((host, port))
				data = dumps(dict)
				s.send(dumps(int(len(data))))
				s.send(data)
				
				sent=0				
				inputLength = len(myInput)
				while sent < inputLength:
					chunk = s.send(myInput[sent:])
					sent = sent+chunk
				s.shutdown(1)

				# Get the response from the AppServer
				bufsize = 8*1024
				# @@ 2000-04-26 ce: this should be configurable, also we should run some tests on different sizes
				# @@ 2001-01-25 jsl: It really doesn't make a massive difference.  8k is fine and recommended.
				
##				s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('ll',0,5)) #wait for 0.5 seconds for data
				while 1:
					try:
						data = s.recv(bufsize)
						if not data:
							break
						self.processResponse(data)
					except socket.error, e:
						if e[0] == errno.EAGAIN: #timed out
							pass
						# @@ gat 2001-05-30: On Windows, if the server gets shut down after the client has already
						# written to the socket but before the server dispatched that request, the recv
						# causes a WSAECONNRESET (which is a Windows Sockets specific error code).
						# If we get this error, we want to retry because it
						# means the server shut down without ever starting to handle our request.
						# Something similar needs to be done for Unix, but I don't have a Unix box to
						# do any testing on.  Note that we're using a little extra paranoia and
						# checking that self._respData is still empty -- this will prevent us from
						# retrying a request that has already begun to be handled by the app server.
						# Strictly, this paranoia is unnecessary, but it doesn't hurt anything so I put
						# it in.
						#
						# And similar retry code should be put into mod_webkit.c also.
						elif os.name=='nt' and e[0] == errno.WSAECONNRESET and not self._respData:
							raise
						else:
							raise "error receiving response (errno = %d)" % e[0]
				break
			except socket.error:
				# retry
				if retries <= self.setting('NumRetries'):
					retries = retries + 1
					time.sleep(self.setting('SecondsBetweenRetries'))
				else:
					raise 'timed out waiting for app server to respond'

		return self._respData


	def processResponse(self, data):
		""" Process response data as it arrives."""
		self._respData = self._respData + data
		

# @@ 2000-07-10 ce fix this up
import sys, time, socket
from marshal import dumps, loads
try:
	import WebUtils
except ImportError:
	sys.path.append('..')
	import WebUtils
from WebUtils.WebFuncs import HTMLEncode

from Object import Object
from MiscUtils.Configurable import Configurable

class Adapter(Configurable, Object):

	def __init__(self):
		Configurable.__init__(self)
		Object.__init__(self)

	def name(self):
		return self.__class__.__name__

	def defaultConfig(self):
		return {
			'NumRetries':            20,
			'SecondsBetweenRetries': 3
		}

	def configFilename(self):
		return 'Configs/%s.config' % self.name()

	def transactWithAppServer(self, env, myInput, host, port):
		'''Used by subclasses that are communicating with a separate app server via socket.  Returns the unmarshaled response dictionary.'''
		dict = {
				'format': 'CGI',
				'time':   time.time(),
				'environ': env,
				'input':   myInput
				}

		resp = ''
		retries = 0
		while 1:
			try:
				# Send our request to the AppServer
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((host, port))
				s.send(dumps(dict))
				s.shutdown(1)

				# Get the response from the AppServer
				bufsize = 32*1024  # @@ 2000-04-26 ce: this should be configurable, also we should run some tests on different sizes
				resp = ''
				while 1:
					data = s.recv(bufsize)
					if not data:
						break
					resp = resp+data
				break
			except socket.error:
				# partial response then error == no good.
				if resp:
					raise 'got a socket error after a partial response from the app server'
				# retry
				if retries <= self.setting('NumRetries'):
					retries = retries + 1
					time.sleep(self.setting('SecondsBetweenRetries'))
				else:
					raise 'timed out waiting for app server to respond'
		return loads(resp)


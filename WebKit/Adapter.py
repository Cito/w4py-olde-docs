import os, sys, time, socket
from marshal import dumps, loads
from Object import Object
from MiscUtils.Configurable import Configurable
from WebUtils.WebFuncs import HTMLEncode


class Adapter(Configurable, Object):

	def __init__(self, webKitDir):
		Configurable.__init__(self)
		Object.__init__(self)
		self._webKitDir = webKitDir

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
			#	'input':   myInput
				}

		resp = ''
		retries = 0
		while 1:
			try:
				# Send our request to the AppServer
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((host, port))
				data = dumps(dict)
				s.send(dumps(int(len(data))))
				s.send(data)
				s.send(myInput)
				s.shutdown(1)

				# Get the response from the AppServer
				bufsize = 8*1024
				# @@ 2000-04-26 ce: this should be configurable, also we should run some tests on different sizes
				# @@ 2001-01-25 jsl: It really doesn't make a massive difference.  8k is fine and recommended.
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
		#return loads(resp)
		return resp

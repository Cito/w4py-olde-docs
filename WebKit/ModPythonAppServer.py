###########################################
# mod_python adapter to embed WebKit completely in Apache
#
# This implemetation is based on the standard mod_python handler
# with a custom AppServer and some minor modifications.
#
#
##########################################

"""

Here's how I set up my Apache conf:

<Location /WK >
   SetHandler python-program
   # add the directory that contains this file and the rest of WebKit.  This should be (path to Webware)/WebKit
   PythonPath "sys.path+['/path/to/WebKit']"
   PythonHandler ModPythonAppServer
   PythonDebug
</Location>



You may also send all requests with a .psp extension to WebKit by adding these lines, outside
of any location or directory.

AddHandler python-program .psp
PythonPath "sys.path+['/path/to/WebKit']"
PythonHandler ModPythonAppServer::pspHandler


Now, on to configuration issues.  The big one is that you need to set your Application.config
to use 'File' as the session store.  The reason is that Apache is a multi process webserver,
so the memory option just won't work.  Additionally, if you are running on UNIX,
the whole WebKit process will be running as nobody/apache or whatever user you run apache as.
This means that that user will need to be able to create, at the minimum, files in the "Sessions" directory.

The only compromise you must make in using this AppServer is that you can't have any Application
wide information.  There is no way to share the information across the application.  This means
no hit counters, no chat servers, etc.  You can do those things, but not by the standard WebKit
methods of either stroing the info in the Application instance or using an Applicatino scope Can.
You will need to use either a shared file, which could get messy in a hurry, or use something like
the ZODB.  I plan to implement ZODB as a Kit as soon as I have time, if some one wants to get started
on it, that would be great.  It might also be useful in load balancing.

"""


from mod_python import apache
import time

import sys
import string
import os

# Change the working directory so that all relative paths work out right
os.chdir(os.path.abspath(os.path.dirname(__file__)))

filedir = os.path.abspath(os.path.dirname(__file__))
WebwareDir = os.path.join(filedir+"/../")
sys.path.append(filedir) #This probably isn't necessary, as this should be set in the Apache Configuration
sys.path.append(WebwareDir)


from Adapter import Adapter


debug=0
_adapter = None
bufsize = 32*1024



from AppServer import AppServer
from Application import Application
from modpHandler import ModPythonAdapter


DefaultConfigAppServer = {
	'PrintConfigAtStartUp': 1,
	'Verbose':			  1,
	'PlugInDirs':		[WebwareDir,]
	}


class InProcessAppServer(AppServer):
	"""
	This AppServer is currently essentially a copy of the OneShotAppServer.  I have decided not to inherit
	from OneShot because there is the potential for significant divergence from that class in the future.
	"""

	def isPersistent(self):
		return 0

	def createApplication(self):
		return Application(server=self, useSessionSweeper=0)

	def dispatchRawRequest(self, newRequestDict):
		return self._app.dispatchRawRequest(newRequestDict)


	def config(self):
		"""
		Returns the configuration of the object as a dictionary. This is a combination of
		defaultConfig() and userConfig(). This method caches the config.
		This method is overridden because the default configuration uses a relative directory
		for the PlugInDir.  Since we don't know wehere we are, we need to
		make sure that the PlugInDirs value includes the real Webware location.

		"""
		if self._config is None:
			self._config = self.defaultConfig()
			self._config.update(self.userConfig())
#			self._config['PlugInDirs'].append(WebwareDir)
		return self._config

	def shutDown(self):
		"""
		We need to manually run the sweepSessions funcion at some point.
		Unfortunately, this will only run it on Linux/UNIX with any regularity.  On Windows, processes
		don't start and stop frequently (unless the OS crashes, so maybe its a moot point? :0), so
		this won't be run often enough.
		Anyone have a better idea?
		"""
		self._app.sweepSessions()
		AppServer.shutDown(self)

cleanup_registered = 0

class ModpApacheAdapter(ModPythonAdapter):
	def __init__(self):
		Adapter.__init__(self)
		self._AppServer=InProcessAppServer()

	def shutDown(self, data):
		self._AppServer.shutDown()

	def __del__(self):
		self.shutDown()
		ModPythonAdapter.__del__(self)

	def handler(self, req):
		global cleanup_registered
		if not cleanup_registered:
			req.server.register_cleanup(req._req, self.shutDown)
			cleanup_registered=1
		try:
			# Get input
			myInput = self.input(req)

			# get the apache module to do the grunt work of
			#   building the environment
			env=apache.build_cgi_env(req)

			# Fix up the path
			if not env.has_key('PATH_INFO'): env['PATH_INFO']=req.path_info

			dict = {
				'format': 'CGI',
				'time':   time.time(),
				'environ': env,
				'input':   myInput
				}
			# Communicate with the app server
			respdict = self._AppServer.dispatchRawRequest(dict).response().rawResponse()

			# Respond back to Apache
			self.respond(req, respdict)

		except:
			self.handleException(req)
		return apache.OK


	def pspHandler(self, req):
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
			respdict = self._AppServer.dispatchRawRequest(dict).response().rawResponse()

			# Respond back to Apache
			self.respond(req, respdict)

		except:
			self.handleException(req)
		return apache.OK


if _adapter is None:
	_adapter = ModpApacheAdapter()


def handler(req):
	return _adapter.handler(req)
def pspHandler(req):
	return _adapter.pspHandler(req)

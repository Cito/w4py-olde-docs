#!/usr/bin/env python

from Common import *
from UserDict import UserDict
from Configurable import Configurable
from ExceptionHandler import ExceptionHandler
from Servlet import Servlet
from ServletFactory import *
from UnknownFileType import UnknownFileTypeServletFactory
from types import FloatType
from glob import glob
import Queue
from threading import Lock, Thread
from CanContainer import *

from WebUtils.WebFuncs import HTMLEncode
from WebUtils.HTMLForException import HTMLForException

# @@ import MiddleKit
# @@ from MiddleKit.KeyValueAccess import KeyValueAccess
import MiscUtils.CSV

# Beef up UserDict with the KeyValueAccess base class and custom versions of
# hasValueForKey() and valueForKey(). This all means that UserDict's (such as
# os.environ) are key/value accessible. At some point, this probably needs to
# move somewhere else as other Webware components will need this "patch".
# (@@ 2000-05-07 ce: Plus I just duplicated this from CGIWrapper.py. Doh!)
import MiddleKit
from MiddleKit.KeyValueAccess import KeyValueAccess
if not KeyValueAccess in UserDict.__bases__:
	UserDict.__bases__ = UserDict.__bases__ + (KeyValueAccess,)

	def _UserDict_hasValueForKey(self, key):
		return self.has_key(key)

	def _UserDict_valueForKey(self, key, default=None): # @@ 2000-05-10 ce: does Tombstone fit here and possibly in KeyValueAccess?
		return self.get(key, default)

	setattr(UserDict, 'hasValueForKey', _UserDict_hasValueForKey)
	setattr(UserDict, 'valueForKey', _UserDict_valueForKey)


class ApplicationError(Exception):
	pass


class Application(Configurable,CanContainer):
	"""
	FUTURE
		* 2000-04-09 ce: Automatically open in browser.
		* 2000-04-09 ce: Option to remove HTML comments in responses.
		* 2000-04-09 ce: Option remove unnecessary white space in responses.
		* 2000-04-09 ce: Debugging flag and debug print method.
		* 2000-04-09 ce: A web-based, interactive monitor to the application.
		* 2000-04-09 ce: Record and playback of requests and responses. Useful for regression testing.
		* 2000-04-09 ce: sessionTimeout() and a hook for when the session has timed out.
		* 2000-04-09 ce: pageRefreshOnBacktrack
		* 2000-04-09 ce: terminate() and isTerminating()
		* 2000-04-09 ce: isRefusingNewSessions()
		* 2000-04-09 ce: terminateAfterTimeInterval()
		* 2000-04-09 ce: restoreSessionWithID:inTransaction:
		* 2000-04-09 ce: pageWithNameForRequest/Transaction() (?)
		* 2000-04-09 ce: port() and setPort() (?)
		* 2000-04-09 ce: Adaptors (?)
		* 2000-04-09 ce: Does request handling need to be embodied in a separate object?
			  - Probably, as we may want request handlers for various file types.
		* 2000-04-09 ce: Concurrent request handling (probably through multi-threading)
	"""

	## Init ##

	def __init__(self, server=None, transactionClass=None, sessionClass=None, requestClass=None, responseClass=None, exceptionHandlerClass=None, contexts=None, useSessionSweeper=1):

		Configurable.__init__(self)

		self._server = server

		if transactionClass:
			self._transactionClass = transactionClass
		else:
			from Transaction import Transaction
			self._transactionClass = Transaction

		if sessionClass:
			self._sessionClass = sessionClass
		else:
			from Session import Session
			self._sessionClass = Session

		if requestClass:
			self._requestClass = requestClass
		else:
			from HTTPRequest import HTTPRequest
			self._requestClass = HTTPRequest

		if responseClass:
			self._responseClass = responseClass
		else:
			from HTTPResponse import HTTPResponse
			self._responseClass = HTTPResponse

		if exceptionHandlerClass:
			self._exceptionHandlerClass = exceptionHandlerClass
		else:
			from ExceptionHandler import ExceptionHandler
			self._exceptionHandlerClass = ExceptionHandler

		# Init those ivars
		self._sessions = {}
		self._servletCacheByPath = {}
		self._serverSidePathCacheByPath = {}
		self._serverDir = os.getcwd()
		self._cacheDictLock = Lock()
		self._instanceCacheSize=10 # self._server.setting('ServerThreads') #CHANGED 6/21/00

##		if contexts: #Try to get this from the Config file
##			self._contexts = contexts
##		else: #Get it from Configurable object, which gets it from defaults or the user config file
##			self._contexts = self.setting('Contexts')
		if contexts: #Try to get this from the Config file
			defctxt = contexts
		else: #Get it from Configurable object, which gets it from defaults or the user config file
			defctxt = self.setting('Contexts')
		#New context loading routine
		self._contexts={}
		for i in defctxt.keys():
			self.addContext(i,defctxt[i])

		# Set up servlet factories
		self._factoryList = []  # the list of factories
		self._factoryByExt = {} # a dictionary that maps all known extensions to their factories, for quick look up
		self.addServletFactory(PythonServletFactory(self))
		self.addServletFactory(UnknownFileTypeServletFactory(self))
		# ^ @@ 2000-05-03 ce: make this customizable at least through a method (that can be overridden) if not a config file (or both)

		if self.setting('PrintConfigAtStartUp'):
			self.printConfig()

		print 'Current directory is', os.getcwd()

		self.initializeCans()

		self.running = 1
		if useSessionSweeper:
			self.startSessionSweeper()

	def initializeCans(self):
		"""
		Overhaul by 0.4
		"""
		import CanFactory
		self._canFactory = CanFactory.CanFactory(self,os.path.join(os.getcwd(),'Cans'))

		

	def startSessionSweeper(self):
		self._sessSweepThread=Thread(None, self.sweeperThreadFunc, 'SessionSweeper', (self._sessions,self.setting('SessionTimeout')))
		self._sessSweepThread.start()

	def sweeperThreadFunc(self,sessions,timeout): #JSL, moved this here so I can control it better, later
		"""
		This function runs in a separate thread and cleans out stale sessions periodically.
		"""
		import sys
		count = 0
		frequency = 30 #how often to run *2

		while 1:
			if not self.running:
				break #time to quit
			count = count+1
			if count > frequency:
				currtime=time.time()
				keys=sessions.keys()
				for i in keys:
					if (currtime - sessions[i].lastAccessTime()) > timeout:
						del sessions[i]
				count = 0
			try:
				time.sleep(2)#sleep for 2 secs, then check to see if its time to quit or run
			except IOError, e:
				pass


	def shutDown(self):
		"""
	Called by AppServer when it is shuting down.  The __del__ function of Application probably won't be called due to circular references.
		"""
		del self._canFactory
		del self._sessions
		self._delCans()
		self.running = 0
		del self._factoryByExt
		del self._factoryList
		del self._server
		if hasattr(self, '_sessSweepThread'):
			# We don't always have this, hence the 'if' above
			self._sessSweepThread.join()
			del self._sessSweepThread
		print "Exiting Application"

##	  def __del__(self):
##			  print "Application deleted"



	## Config ##

	def defaultConfig(self):
		return {
			'PrintConfigAtStartUp': 1,
			'DirectoryFile':        ['index', 'Main'],
			'ExtensionsToIgnore':   ['.pyc', '.pyo', '.py~', '.bak'],
			'LogActivity':          1,
			'ActivityLogFilename':  'Logs/Activity.csv',
			'ActivityLogColumns':   ['request.remoteAddress', 'request.method', 'request.uri', 'response.size', 'servlet.name', 'request.timeStamp', 'transaction.duration', 'transaction.errorOccurred'],

			# Error handling
			'ShowDebugInfoOnErrors': 1,
			'UserErrorMessage':      'The site is having technical difficulties with this page. An error has been logged, and the problem will be fixed as soon as possible. Sorry!',
			'ErrorLogFilename':      'Logs/Errors.csv',
			'SaveErrorMessages':     1,
			'ErrorMessagesDir':      'ErrorMsgs',
			'EmailErrors':           0, # be sure to review the following settings when enabling error e-mails
			'ErrorEmailServer':      'mail.-.com',
			'ErrorEmailHeaders':     { 'From':         '-@-.com',
			                           'To':           ['-@-.com'],
			                           'Reply-to':     '-@-.com',
			                           'Content-type': 'text/html',
			                           'Subject':      'Error'
			                         },
			'Contexts':              { 'default':       'Examples',
			                           'Admin':         'Admin',
			                           'Examples':      'Examples',
			                           'Documentation': 'Documentation',
			                           'Testing':       'Testing',
			                         },
			'SessionTimeout':        60*60, # seconds
		}

	def configFilename(self):
		return 'Configs/Application.config'


	## Versions ##

	def webwareVersion(self):
		''' Returns the version of Webware as a string as taken from the file ../_VERSION. '''
		if not hasattr(self, '_webwareVersion'):
			s = open('../_VERSION').readlines()[0]
			s = string.strip(s[len('Webware'):])
			self._webwareVersion = s
		return self._webwareVersion

	def webKitVersion(self):
		return '0.4 PR 1'

	def version(self):
		"""
		Returns the version of the application. This implementation returns '0.1'. Subclasses should override to return the correct version number.
		"""
		## @@ 2000-05-01 ce: Maybe this could be a setting 'AppVersion'
		return '0.1'


	## Dispatching Requests ##

	def dispatchRawRequest(self, newRequestDict):
		return self.dispatchRequest(self.createRequestForDict(newRequestDict))

	def dispatchRequest(self, request):
		"""
		Creates the transaction, session, response and servlet for the new request which is then dispatched. The transaction is returned.
		"""
		transaction = None
		if request.value('_captureOut_', 0):
			real_stdout = sys.stdout
			sys.stdout = StringIO()

		transaction = self.createTransactionForRequest(request)
		response	= self.createResponseInTransaction(transaction)

		try:
			ssPath = request.serverSidePath()
			if ssPath is None:
				self.handleBadURL(transaction)
			elif isdir(ssPath) and noslash(request.pathInfo()): # (*) see below
				self.fixDirectoryURL(transaction)
			else:
				self.serveURL(transaction)

			if request.value('_captureOut_', 0):
				response.write('''<br><p><table><tr><td bgcolor=#EEEEEE>
					<pre>%s</pre></td></tr></table>''' % sys.stdout.getvalue())
				sys.stdout = real_stdout

			response.deliver(transaction)

			# (*) We have to use pathInfo() instead of uri() when looking for the trailing slash, because some webservers, notably Apache, append a trailing / to REQUEST_URI in some circumstances even though the user did not specify that (for example: http://localhost/WebKit.cgi).

		except:
			if transaction:
				transaction.setErrorOccurred(1)
			self.handleExceptionInTransaction(sys.exc_info(), transaction)
			transaction.response().deliver(transaction) # I hope this doesn't throw an exception. :-)   @@ 2000-05-09 ce: provide a secondary exception handling mechanism
			pass

		if self.setting('LogActivity'):
			self.writeActivityLog(transaction)

		path = request.serverSidePath()
		self.returnInstance(transaction, path)

		# possible circular reference, so delete it
		# @@ 2000-06-26 ce: we should have a more general solution for this
		request._transaction = None

		return transaction

	def handleBadURL(self, transaction):
		res = transaction.response()
		res.setHeader('Status', 404)
		res.write('<p> 404 Not found: %s' % transaction.request().uri())
		# @@ 2000-06-26 ce: This error page is pretty primitive
		# @@ 2000-06-26 ce: We should probably load a separate template file and display that

	def fixDirectoryURL(self, transaction):
		newURL = transaction.request().uri() + '/'
		res = transaction.response()
		res.setHeader('Status', '301')
		res.setHeader('Location', newURL)
		res.write('''<html>
	<head>
		<title>301 Moved Permanently</title>
	</head>
	<body>
		<h1>Moved Permanently</h1>
		<p> The document has moved to <a href="%s">%s</a>.
	</body>
</html>''' % (newURL, newURL))

	def serveURL(self, transaction):
		#session	 = self.createSessionForTransaction(transaction)
		self.createServletInTransaction(transaction)
		self.awake(transaction)
		self.respond(transaction)
		self.sleep(transaction)

	def forwardRequest(self, trans, URL):
		"""
		Enable a servlet to pass a request to another servlet.  This implementation handles chaining and requestDispatch in Java.
		The catch is that the function WILL return to the calling servlet, so the calling servlet should either take advantage of that or return immediately.
		Currently the URL is always relative to the existing URL.
		"""

		req = trans.request()

		# URL is relative to the original
		urlPath = req.urlPath()
		if urlPath=='':
			urlPath = '/' + URL
		elif urlPath[-1]=='/':
			urlPath = urlPath + URL
		else:
			lastSlash = string.rfind(urlPath, '/')
			urlPath = urlPath[:lastSlash+1] + URL

		newRequest = self.createRequestForDict(req.rawRequest())
		newRequest.setURLPath(urlPath)
		newTrans = self.dispatchRequest(newRequest)
		trans.response().appendRawResponse(newTrans.response().rawResponse())
		return

		# Save the things we're gonna change.
		currentPath = req.serverSidePath()
		currentServlet = trans.servlet()

		# Get the path to the next servlet.
		req.setURLPath(urlPath)
#			   req._serverSidePath = self.serverSidePathForRequest(req)

		# Get the servlet
		self.dispatchRequest(req)

		if 0:
			# the old way
			self.createServletInTransaction(trans)

			# Call the servlet, but not session, it's already alive
			trans.servlet().awake(trans)
			trans.servlet().respond(trans)
			trans.servlet().sleep(trans)

			self.returnInstance(trans, req.serverSidePath())

		# Replace things like they were
		req.setURLPath(currentPath)
		trans.setServlet(currentServlet)


	## Transactions ##

	# @@ 2000-05-10 ce: should just send the message to the transaction and let it handle the rest.

	def awake(self, transaction):
		if transaction._session:
			transaction.session().awake(transaction)
		transaction.servlet().awake(transaction)

	def respond(self, transaction):
		if transaction._session:
			transaction.session().respond(transaction)
		transaction.servlet().respond(transaction)

	def sleep(self, transaction):
		if transaction._session:
			transaction.session().sleep(transaction)
		transaction.servlet().sleep(transaction)


	## Sessions ##

	def session(self, sessionId, default=Tombstone):
		if default is Tombstone:
			return self._sessions[sessionId]
		else:
			return self._sessions.get(sessionId, default)

	def hasSession(self, sessionId):
		return self._sessions.has_key(sessionId)

	def sessions(self):
		return self._sessions


	## Misc Access ##

	def server(self):
		return self._server

	def name(self):
		return sys.argv[0]

	def transactionClass(self):
		return self._transactionClass

	def setTransactionClass(self, newClass):
		assert isclass(newClass)
		self._transactionClass = newClass

	def responseClass(self, newClass):
		return self._responseClass

	def setResponseClass(self, newClass):
		assert isclass(newClass)
		self._responseClass = newClass


	## Contexts ##

	def context(self, name, default=Tombstone):
		''' Returns the value of the specified context. '''
		if default is Tombstone:
			return self._contexts[name]
		else:
			return self._contexts.get(name, default)

	def hasContext(self, name):
		return self._contexts.has_key(name)

	def _setContext(self, name, value):#use addContext
		if self._contexts.has_key(name):
			print 'WARNING: Overwriting context %s (=%s) with %s' % (
				repr(name), repr(self._contents[name]), repr(value))
		self._contexts[name] = value

	def contexts(self):
		return self._contexts

	def addContext(self, name, dir):
		import imp
		if self._contexts.has_key(name):
			print 'WARNING: Overwriting context %s (=%s) with %s' % (
				repr(name), repr(self._contents[name]), repr(value))
		try:
			localdir,pkgname = os.path.split(dir)
			res = imp.find_module(pkgname,[localdir])
			#question, do we want the package name to be the dir name or the context name?
			imp.load_module(name,res[0],res[1],res[2]) 
		except:
			print "%s is not a package" % (name,)
		self._contexts[name] = dir



	## Factory access ##

	def addServletFactory(self, factory):
		assert isinstance(factory, ServletFactory)
		self._factoryList.append(factory)
		for ext in factory.extensions():
			assert not self._factoryByExt.has_key(ext), 'Extension (%s) for factory (%s) was already used by factory (%s)' % (ext, self._factoryByExt[ext].name(), factory.name())
			self._factoryByExt[ext] = factory

	def factories(self):
		return self._factoryList


	## Activity Log ##

	def writeActivityLog(self, transaction):
		"""
		Writes an entry to the script log file. Uses settings ActivityLogFilename and ActivityLogColumns.
		"""
		filename = os.path.join(self._serverDir, self.setting('ActivityLogFilename'))
		if os.path.exists(filename):
			file = open(filename, 'a')
		else:
			file = open(filename, 'w')
			file.write(string.join(self.setting('ActivityLogColumns'), ',')+'\n')
		values = []
		# We use UserDict on the next line because we know it inherits KeyValueAccess and reponds to valueForName()
		objects = UserDict({
			'application': self,
			'transaction': transaction,
			'request':	 transaction.request(),
			'response':	transaction.response(),
			'servlet':	 transaction.servlet(),
			'session':	 transaction._session, #don't cause creation of session
		})
		for column in self.setting('ActivityLogColumns'):
			try:
				value = objects.valueForName(column)
			except:
				print 'WARNING: Cannot get %s for activity log.' % column
				value = '(unknown)'
			if type(value) is FloatType:
				value = '%0.2f' % value   # probably need more flexibility in the future
			else:
				value = str(value)
			values.append(value)
		file.write(string.join(values, ',')+'\n')
		file.close()

		for i in objects.keys():
			objects[i]=None


	## Utilities/Hooks ##

	def serverDir(self):
		"""
		Returns the directory where the application server is located.
		"""
		return self._serverDir

	def createRequestForDict(self, newRequestDict):
		return self._requestClass(dict=newRequestDict)

	def createTransactionForRequest(self, request):
		trans = self._transactionClass(application=self, request=request)
		request.setTransaction(trans)
		return trans

	def createResponseInTransaction(self, transaction):
		response = self._responseClass()
		transaction.setResponse(response)
		return response

	def createSessionForTransaction(self, transaction):
		#print "Creating Session"
		sessId = transaction.request().sessionId()
		session = None
		if sessId:
			session = self.session(sessId, None)
		# @@ 2000-05-10 ce: So here we just make a new session if the existing session id is invalid. Is that really the behavior we want? At the very least, we should probably have a "hook" method that subclasses can customize
		if session is None:
			session = self._sessionClass(transaction)
			self._sessions[session.identifier()] = session
		transaction.setSession(session)
		return session

	def _original_createServletInTransaction(self, transaction):
		# Get the path and extension
		path = transaction.request().serverSidePath()

		# Cached?
		cache = self._servletCacheByPath.get(path, None)

		# File is not newer?
		if cache and self._servletCacheByPath[path]['timestamp']<os.path.getmtime(path):
			cache = None

		# Instance can be reused?
		if cache and not cache['instance'].canBeReused():
			cache = None

		# Create the cache?
		if not cache:
			# Add the path to sys.path. @@ 2000-05-09 ce: not the most ideal solution, but works for now
			dir = os.path.split(path)[0]

			if not dir in sys.path:
				sys.path.insert(0, dir)

			# Get the factory responsible for making this servlet
			ext = os.path.splitext(path)[1]
			factory = self._factoryByExt.get(ext, None)
			if not factory:
				factory = self._factoryByExt.get('.*', None) # special case: .* is the catch-all
				if not factory:
					raise ApplicationError, 'Unknown extension (%s). No factory found.' % ext
					# ^ @@ 2000-05-03 ce: Maybe the web browser doesn't want an exception for bad extensions. We probably need a nicer message to the user...
					#					 On the other hand, that can always be done by providing a factory for '.*'
			assert factory.uniqueness()=='file', '%s uniqueness is not supported.' % factory.uniqueness()

			# Get the servlet and create the cache
			cache = {
				'instance':  factory.servletForTransaction(transaction),
				'path':	  path,
				'timestamp': os.path.getmtime(path)
			}
			assert cache['instance'] is not None, 'Factory (%s) failed to create a servlet upon request.' % factory.name()
			self._servletCacheByPath[path] = cache

		# Set the transaction's servlet
		transaction.setServlet(cache['instance'])

	##JSL
	def getServlet(self, transaction, path, cache=None): #send the cache if you want the cache info set
		ext = os.path.splitext(path)[1]
		# Add the path to sys.path. @@ 2000-05-09 ce: not the most ideal solution, but works for now
		dir = os.path.split(path)[0]

		factory = self._factoryByExt.get(ext, None)
		if not factory:
			factory = self._factoryByExt.get('.*', None) # special case: .* is the catch-all
			if not factory:
				raise ApplicationError, 'Unknown extension (%s). No factory found.' % ext
			# ^ @@ 2000-05-03 ce: Maybe the web browser doesn't want an exception for bad extensions. We probably need a nicer message to the user...
			#					 On the other hand, that can always be done by providing a factory for '.*'
		assert factory.uniqueness()=='file', '%s uniqueness is not supported.' % factory.uniqueness()

		if not dir in sys.path:
			sys.path.insert(0, dir)
		inst = factory.servletForTransaction(transaction)
		assert inst is not None, 'Factory (%s) failed to create a servlet upon request.' % factory.name()

		if cache:
			cache['threadsafe']=inst.canBeThreaded()
			cache['reuseable']=inst.canBeReused()
		return inst

	def returnInstance(self, transaction, path):
		""" The only case I care about now is threadsafe=0 and reuseable=1"""
		cache = self._servletCacheByPath.get(path, None)
		if cache and cache['reuseable'] and not cache['threadsafe']:
			try:
				srv = transaction.servlet()
				if srv:
					cache['instances'].put(transaction.servlet())
					#cache['instances'].put_nowait(transaction.servlet())
					#print "returned Instance"
					return
				else:
					#error in executing servlet, drop it?
					cache['created'] = cache['created']-1
			except Queue.Full: #full or blocked
				pass
				print '>> queue full for:',cache['path'] #do nothing, don't want to block queue for this

##			  print ">> Deleting Servlet: ",sys.getrefcount(transaction._servlet)



	def newServletCacheItem(self,key,item):
		""" Safely add new item to the main cache.  Not woried about the retrieval for now.
		I'm not even sure this is necessary, as it's a one bytecode op, but it doesn't cost much of anything speed wise."""
		#self._cacheDictLock.acquire()
		self._servletCacheByPath[key] = item
		#self._cacheDictLock.release()


	def createServletInTransaction(self, transaction):
		# Get the path
		path = transaction.request().serverSidePath()
		assert path is not None

		inst = None

		# Cached?
		cache = self._servletCacheByPath.get(path, None)

		# File is not newer?
		if cache and cache['timestamp']<os.path.getmtime(path):
			try:
				while cache['instances'].qsize > 0: # don't leave instances out there, right?
					cache['instances'].get_nowait()
				cache = None
			except Queue.Empty:
				cache = None

		if not cache:
			cache = {
				'instances':  Queue.Queue(self._instanceCacheSize+1), # +1 is for safety
				'path':	   path,
				'timestamp':  os.path.getmtime(path),
				'threadsafe': 0,
				'reuseable':  0,
				'created':	1,
				'lock':	   Lock(), # used for the created count
				}

			self.newServletCacheItem(path,cache)
			inst = self.getServlet(transaction,path,cache)

			if cache['threadsafe']:
				"""special case, put in the cache now"""
				cache['instances'].put(inst)


		# Instance can be reused?
		elif not cache['reuseable']:
			"""One time servlet"""
			inst = self.getServlet(transaction, path)

		elif not cache['threadsafe']:
			""" Not threadsafe, so need multiple instances"""
##					  print '>> Queue size:', cache['instances'].qsize()
			try:
				inst = cache['instances'].get_nowait()
			except Queue.Empty: #happens if empty or blocked
				cache['lock'].acquire()
				if cache['created'] < self._instanceCacheSize:
					inst = self.getServlet(transaction, path) # really need to create a new one
					cache['created'] = cache['created']+1
				else:
					inst = cache['instances'].get() # block, it's really there
				cache['lock'].release()


		# Must be reuseable and threadsafe, get it and put it right back, I'm assuming this will be a rare case
		else:
			inst = cache['instances'].get()
			cache['instances'].put(inst)

		# Set the transaction's servlet
		transaction.setServlet(inst)

	##END JSL threadpool

	def handleExceptionInTransaction(self, excInfo, transaction):
		self._exceptionHandlerClass(self, transaction, excInfo)

	def filenamesForBaseName(self, baseName, debug=0):
		'''
		Returns a list of all filenames with extensions existing for baseName, but not including extension found in the setting ExtensionsToIgnore. This utility method is used by serverSidePathForRequest().
		Example: '/a/b/c' could yield ['/a/b/c.py', '/a/b/c.html'], but will never yield a '/a/b/c.pyc' filename since .pyc files are ignored.
		'''
		filenames = glob(baseName+'.*')
		ignoreExts = self.setting('ExtensionsToIgnore')
		for i in range(len(filenames)):
			if os.path.splitext(filenames[i])[1] in ignoreExts: # @@ 2000-06-22 ce: linear search
				filenames[i] = None
		filenames = filter(None, filenames)
		if debug:
			print '>> filenamesForBaseName(%s) returning %s' % (
				repr(baseName), repr(filenames))
		return filenames

	def serverSidePathForRequest(self, request, debug=0):
		"""
		Returns what it says. This is a 'private' service method for use by HTTPRequest.
		Returns None if there is no corresponding server side path for the URL.

		This method supports:
			* Contexts
			* A default context
			* Auto discovery of directory vs. file
			* For directories, auto discovery of file, configured by DirectoryFile
			* For files, auto discovery of extension, configured by ExtensionsToIgnore
			* Rejection of files (not directories) that end in a slash (/)
			* NOT YET: "Extra path" URLs where the servlet is actually embedded in the path
			  as opposed to being at the end of it. (ex: http://foo.com/servlet/extra/path)

		IF YOU CHANGE THIS VERY IMPORTANT, SUBTLE METHOD, THEN PLEASE REVIEW
		AND COMPLETE http://localhost/WebKit.cgi/Testing/ BEFORE CHECKING IN
		OR SUBMITTING YOUR CHANGES.
		"""

		if debug:
			print '>> serverSidePathForRequest(request=%s)' % repr(request)
			import pprint
			pprint.pprint(request._rawRequest)

		urlPath = request.urlPath()
		if debug: print '>> urlPath =', repr(urlPath)

		# try the cache first
		ssPath = self._serverSidePathCacheByPath.get(urlPath, None)
		if ssPath is not None:
			if debug: print '>> returning path from cache: %s' % repr(ssPath)
			return ssPath

		# check for extraPathInfo type url in cache, like http://localhost/SomeServlet/e/p/i
		if 0: # @@ 2000-06-22 ce: disabled, have to rethink the logic here
			if debug: print '>> looking for extraPathInfo type url in cache'
			extraPathInfo = ''
			strippedPath = urlPath
			while strippedPath!='' and ssPath==None:
				strippedPath, extraPathInfo = os.path.split(strippedPath)
				ssPath = self._serverSidePathCacheByPath.get(strippedPath, None)
				#if extraPathInfo!='': # avoid a trailing /
				#	   extraPathInfo = os.path.join(extra, extraPathInfo)
				#else:
				#	   extraPathInfo = extra
			if ssPath==None:
				# we failed to find one in the cache
				extraPathInfo = ''
				if debug: print '>> did not find one'
			else:
				request._fields['extraPathInfo'] = extraPathInfo
				if debug:
					print '>> returning path %s with extraPathInfo %s' % (
						repr(ssPath), extraPathInfo)
				return ssPath

		# case: no URL then use the default context
		if urlPath=='' or urlPath=='/':
			fspath = request.fsPath()
			if debug:
				print "fsPath: %s"%fspath
			if os.path.exists(fspath):
				return fspath
			ssPath = self._contexts['default']
			if urlPath=='': urlPath='/'
			if debug:
				print '>> no urlPath, so using default context path: %s' % repr(ssPath)
		else:
			# Check for and process context name:
			assert urlPath[0]=='/', 'urlPath=%s' % repr(urlPath)
			if string.rfind(urlPath, '/')>0: # no / in url (other than the preceding /)
				blank, contextName, restOfPath = string.split(urlPath, '/', 2)
			else:
				contextName, restOfPath = urlPath[1:], ''
			if debug: print '>> contextName=%s, restOfPath=%s' % (repr(contextName), repr(restOfPath))

			# Look for context
			try:
				prepath = self._contexts[contextName]
			except KeyError:
				restOfPath = urlPath[1:]  # put the old path back, there's no context here
				prepath = self._contexts['default']
				if debug:
					print '>> context not found so assuming default:'
			if debug: print '>> prepath=%s, restOfPath=%s' % (repr(prepath), repr(restOfPath))
			ssPath = os.path.join(prepath, restOfPath)

		lastChar = ssPath[-1]
		ssPath = os.path.normpath(ssPath)

		# 2000-07-06 ce: normpath() chops off a trailing / (or \)
		# which is NOT what we want. This makes the test case
		# http://localhost/WebKit.cgi/Welcome/ pass when it should
		# fail. URLs that name files must not end in slashes because
		# relative URLs in the resulting document will get appended
		# to the URL, instead of replacing the last component.
		if lastChar=='\\' or lastChar=='/':
			ssPath = ssPath + os.sep

		if debug: print '>> normalized ssPath =', repr(ssPath)

		if 0: # @@ 2000-06-22 ce: disabled, have to rethink the logic here
			extraPathInfo=''
			if not isdir(os.path.split(ssPath)[0]):
				while restOfPath != '':  #don't go too far
					if not isdir(os.path.join(basePath,os.path.split(restOfPath)[0])): #strip down to the first real directory
						restOfPath,extra = os.path.split(restOfPath)
						if extraPathInfo != '': #avoid a trailing '/'
							extraPathInfo=os.path.join(extra,extraPathInfo)
						else:
							extraPathInfo=extra
					else: # if I get here, I'm either at the real Servlet, or I'm at basePath
						ssPath = os.path.join(basePath,restOfPath)
						urlPath = urlPath[:string.rindex(urlPath,extraPathInfo)-1]#remove trailing /
						break

		if isdir(ssPath):
			# URLs that map to directories need to have a trailing slash.
			# If they don't, then relative links in the web page will not be
			# constructed correctly by the browser.
			# So in the following if statement, we're bailing out for such URLs.
			# dispatchRequest() will detect the situation and handle the redirect.
			if urlPath=='' or urlPath[-1]!='/':
				if debug:
					print '>> BAILING on directory url: %s' % repr(urlPath)
				return ssPath

			# Handle directories
			if debug: print '>> directory = %s' % repr(ssPath)
			for dirFilename in self.setting('DirectoryFile'):
				filenames = self.filenamesForBaseName(os.path.join(ssPath, dirFilename), debug)
				num = len(filenames)
				if num==1:
					break  # we found a file to handle the directory
				elif num>1:
					print 'WARNING: For %s, the directory is %s which contains more than 1 directory file: %s' % (urlPath, ssPath, filenames)
					return None
			if num==0:
				print 'WARNING: For %s, the directory is %s which contains no directory file.' % (urlPath, ssPath)
				return None
			ssPath = filenames[0] # our path now includes the filename within the directory
			if debug: print '>> discovered directory file = %s' % repr(ssPath)

		elif os.path.splitext(ssPath)[1]=='':
			# At this point we have a file (or a bad path)
			filenames = self.filenamesForBaseName(ssPath, debug)
			if len(filenames)==1:
				ssPath = filenames[0]
				if debug: print '>> discovered extension, file = %s' % repr(ssPath)
			else:
				print 'WARNING: For %s, did not get precisely 1 filename: %s' % (urlPath, filenames)
				return None

		self._serverSidePathCacheByPath[urlPath] = ssPath
		if 0: # @@ 2000-06-22 ce: disabled, have to rethink the logic here
			if extraPathInfo:
				request._fields['extraPathInfo'] = extraPathInfo

		if debug:
			print '>> returning %s\n' % repr(ssPath)
		return ssPath


def isdir(s):
	'''
	*** Be sure to use this isdir() function rather than os.path.isdir()
		in this file.

	2000-07-06 ce: Only on Windows, does an isdir() call with a
	path ending in a slash fail to return 1. e.g.,
	isdir('C:\\tmp\\')==0 while on UNIX isdir('/tmp/')==1.
	'''
	if s and os.name=='nt' and s[-1]==os.sep:
		return os.path.isdir(s[:-1])
	else:
		return os.path.isdir(s)

def noslash(s):
	''' Return 1 if s is blank or does end in /.  A little utility for dispatchRequest(). '''
	return s=='' or s[-1]!='/'


def main(requestDict):
	"""
	Returns a raw reponse. This method is mostly used by OneShotAdaptor.py.
	"""
	from WebUtils.HTMLForException import HTMLForException
	try:
		assert type(requestDict) is type({})
		app = Application(useSessionSweeper=0)
		return app.dispatchRawRequest(requestDict).response().rawResponse()
	except:
		return {
			'headers': [('Content-type', 'text/html')],
			'contents': '<html><body>%s</html></body>' % HTMLForException()
		}


# You can run Application as a main script, in which case it expects a single
# argument which is a file containing a dictionary representing a request. This
# technique isn't very popular as Application itself could raise exceptions
# that aren't caught. See CGIAdaptor.py and AppServer.py for a better example of
# how things should be done.
if __name__=='__main__':
	if len(sys.argv)!=2:
		sys.stderr.write('WebKit: Application: Expecting one filename argument.\n')
	requestDict = eval(open(sys.argv[1]).read())
	main(requestDict)

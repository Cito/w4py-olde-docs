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



try:
	import WebUtils
except:
	sys.path.append('..')
	import WebUtils
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
		* 2000-04-09 ce: Actions: URLs that are bound to specific methods of a servlet
			  - These could be powerful, because they could send the request back to the
				same object that generated the page, but invoke a different method.
				That's useful for at least forms processing and it's kind of like buttons
				on a GUI window that tie back to the same controller.
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

	def __init__(self, server=None, transactionClass=None, sessionClass=None, requestClass=None, responseClass=None, exceptionHandlerClass=None, Contexts=None, useSessionSweeper=1):


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
		self._instanceCacheSize=self._server.setting('ServerThreads') #CHANGED 6/21/00

		if Contexts: #Try to get this from the Config file
			self._Contexts = Contexts
		else: #Get it from Configurable object, which gets it from defaults or the user config file
			self._Contexts=self.setting('Contexts')

		# Set up servlet factories
		self._factoryList = []  # the list of factories
		self._factoryByExt = {} # a dictionary that maps all known extensions to their factories, for quick look up
		self.addServletFactory(PythonServletFactory(self))
		self.addServletFactory(UnknownFileTypeServletFactory(self))
		# ^ @@ 2000-05-03 ce: make this customizable at least through a method (that can be overridden) if not a config file (or both)

		if self.setting('PrintConfigAtStartUp'):
			self.printConfig()

		print 'Current directory is', os.getcwd()

		#JSL
		import CanFactory
		self._canFactory = CanFactory.CanFactory(self,os.path.join(os.getcwd(),'Cans'))
		#JSL

		#JSL
		self.running = 1
		if useSessionSweeper:
			self._startSessionSweeper()


	def _startSessionSweeper(self):
		self._sessSweepThread=Thread(None, self.Sweeper, 'SessionSweeper', (self._sessions,self.setting('SessionTimeout')))
		self._sessSweepThread.start()

	def Sweeper(self,sessions,timeout): #JSL, moved this here so I can control it better, later
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
		""" Called by AppServer when it is shuting down.  The __del__ function of Application probably won't be called due to circular references."""
		del self._canFactory
		del self._sessions
		self._delCans()
		self.running = 0
		#self._sessSweepThread.join()
		print "Exiting Application"

##	def __del__(self):
##		print "Application deleted"



	## Config ##

	def defaultConfig(self):
		return {
			'PrintConfigAtStartUp': 1,
			'ServletsDir':          'Examples',
			'ExtensionsToIgnore':	['.pyc', '.pyo', '.py~', '.bak'],
			'LogActivity':          1,
			'ActivityLogFilename':  'Logs/Activity.csv',
			'ActivityLogColumns':   ['request.remoteAddress', 'request.method', 'request.uri', 'response.size', 'servlet.name', 'request.timeStamp', 'transaction.duration', 'transaction.errorOccurred'],

			# Error handling
			'ShowDebugInfoOnErrors':  1,
			'UserErrorMessage':       'The site is having technical difficulties with this page. An error has been logged, and the problem will be fixed as soon as possible. Sorry!',
			'ErrorLogFilename':       'Logs/Errors.csv',
			'SaveErrorMessages':      1,
			'ErrorMessagesDir':       'ErrorMsgs',
			'EmailErrors':            0, # be sure to review the following settings when enabling error e-mails
			'ErrorEmailServer':       'mail.-.com',
			'ErrorEmailHeaders':      { 'From':         '-@-.com',
				                        'To':           ['-@-.com'],
				                        'Reply-to':     '-@-.com',
				                        'Content-type': 'text/html',
				                        'Subject':      'Error'
									  },
			'Contexts':               { 'default':  'Examples',
							            'Examples': 'Examples',
			                          },
			'SessionTimeout':         60*60, # seconds
		}

	def configFilename(self):
		return 'Configs/Application.config'


	## Versions ##

	def webKitVersion(self):
		return '0.3'

	def version(self):
		"""
		Returns the version of the application. This implementation returns '0.1'. Subclasses should override to return the correct version number.
		"""
		## @@ 2000-05-01 ce: Maybe this could be a setting 'AppVersion'
		return '0.1'


	## Dispatching Requests ##

	def dispatchRawRequest(self, newRequestDict):
		return self.dispatchRequest(self.createRequestForDict(newRequestDict))


	def dispatchRequest(self, newRequest):
		"""
		Creates the transaction, session, response and servlet for the new request which is then dispatched. The transaction is returned.
		"""
		transaction = None
		try:
			request     = newRequest
			transaction = self.createTransactionForRequest(request)
			session     = self.createSessionForTransaction(transaction)
			response    = self.createResponseInTransaction(transaction)
			self.createServletInTransaction(transaction)

			self.awake(transaction)
			self.respond(transaction)
			self.sleep(transaction)

			transaction.response().deliver(transaction)

		except:
			if transaction:
				transaction.setErrorOccurred(1)
			self.handleExceptionInTransaction(sys.exc_info(), transaction)
 			transaction.response().deliver(transaction) # I hope this doesn't throw an exception. :-)   @@ 2000-05-09 ce: provide a secondary exception handling mechanism
			pass

		if self.setting('LogActivity'):
			self.writeActivityLog(transaction)

		path = transaction._request.serverSidePath()
		self.returnInstance(transaction,path)

		#possible circular reference, so delete it
		transaction._request._transaction=None
		return transaction

	def forwardRequest(self, trans, URL):
		"""Enable a servlet to pass a request to another servlet.  This implementation handles chaining and requestDispatch in Java.
		The catch is that the function WILL return to the calling servlet, so the calling servlet should either take advantage
		of that or return immediately."""

		#Save the things we're gonna change.
		currentPath=trans.request().serverSidePath()
		currentServlet=trans._servlet

		#get the path to the next servlet.
		trans.request()._serverSidePath=self.serverSidePathForRequest(trans.request(),URL)

		#Get the servlet
		self.createServletInTransaction(trans)

		#call the servlet, but not session, it's already alive
		trans.servlet().awake(trans)
		trans.servlet().respond(trans)
		trans.servlet().sleep(trans)

		self.returnInstance(trans,trans.request().serverSidePath())

		#replace things like they were
		trans.request()._serverSidePath=currentPath
		trans._servlet=currentServlet



	## Transactions ##

	# @@ 2000-05-10 ce: should just send the message to the transaction and let it handle the rest.

	def awake(self, transaction):
		transaction.session().awake(transaction)
		transaction.servlet().awake(transaction)

	def respond(self, transaction):
		transaction.session().respond(transaction)
		transaction.servlet().respond(transaction)

	def sleep(self, transaction):
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
			'request':     transaction.request(),
			'response':    transaction.response(),
			'servlet':     transaction.servlet(),
			'session':     transaction.session()
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
					#                     On the other hand, that can always be done by providing a factory for '.*'
			assert factory.uniqueness()=='file', '%s uniqueness is not supported.' % factory.uniqueness()

			# Get the servlet and create the cache
			cache = {
				'instance':  factory.servletForTransaction(transaction),
				'path':      path,
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
			#                     On the other hand, that can always be done by providing a factory for '.*'
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
		if cache['reuseable'] and not cache['threadsafe']:
			try:
				cache['instances'].put(transaction.servlet())
				#cache['instances'].put_nowait(transaction.servlet())
				#print "returned Instance"
				return
			except Queue.Full: #full or blocked
				pass
				print '>> queue full for:',cache['path'] #do nothing, don't want to block queue for this

##		print ">> Deleting Servlet: ",sys.getrefcount(transaction._servlet)



	def newServletCacheItem(self,key,item):
		""" Safely add new item to the main cache.  Not woried about the retrieval for now.
		I'm not even sure this is necessary, as it's a one bytecode op, but it doesn't cost much of anything speed wise."""
		#self._cacheDictLock.acquire()
		self._servletCacheByPath[key]=item
		#self._cacheDictLock.release()


	def createServletInTransaction(self, transaction):
		# Get the path
		path = transaction.request().serverSidePath()
		assert path is not None

		inst = None

		# Cached?
		cache = self._servletCacheByPath.get(path, None)

		# File is not newer?
		if cache and self._servletCacheByPath[path]['timestamp']<os.path.getmtime(path):
			try:
				while cache['instances'].qsize > 0: #don't leave instances out there, right?
					cache['instances'].get_nowait()
				cache = None
			except Queue.Empty:
				pass

		if not cache:
			cache = {
				'instances':  Queue.Queue(self._instanceCacheSize+1), # +1 is for safety
				'path':       path,
				'timestamp':  os.path.getmtime(path),
				'threadsafe': 0,
				'reuseable':  0,
				'created':1,
				'lock': Lock(),#used for the created count
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
##			print '>> Queue size:', cache['instances'].qsize()
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

	def serverSidePathForRequest(self, request, urlPath):
		""" Returns what it says. This is a 'private' service method for use by HTTPRequest. """
		extraPathInfo=''
		ssPath = self._serverSidePathCacheByPath.get(urlPath, None)
		
		if ssPath is not None:
			return ssPath #get out now!
		else: #check for extraPathInfo type url in cache
			strippedPath = urlPath
			while strippedPath != '' and ssPath == None:
				strippedPath,extra=os.path.split(strippedPath)
				ssPath = self._serverSidePathCacheByPath.get(strippedPath, None)
				if extraPathInfo != '': #avoid a trailing os.sep
					extraPathInfo=os.path.join(extra,extraPathInfo)
				else: extraPathInfo=extra
				
   		if ssPath is not None:
			request._fields['extraPathInfo']=extraPathInfo
			return ssPath  #get out now!


		else:
			if not urlPath: urlPath = os.path.join(self._Contexts['default'],"index.html") #handle no filename, should be configurable
			if urlPath[0]=='_':  # special administration scripts are denoted by a preceding underscore and are located with the app server. @@ 2000-05-19 ce: redesign this
				ssPath = os.path.join(self.serverDir(), urlPath)
			else:
				#handle case of no /
				if string.find(urlPath,os.sep) > -1: 
					contextName,restOfPath = string.split(urlPath,os.sep,1) #is this OS specific????
				else:
					contextName = urlPath

				#Look for Context
				try:
					prepath = self._Contexts[contextName]
				except KeyError:
					#print '>> Context Not Found'
					restOfPath=urlPath #put the old path back, there's no context here
					prepath = self._Contexts['default']

				#is this an absolute path?  If not, make it one
				if not os.path.isabs(prepath):
					basePath = os.path.join(self.serverDir(), prepath)
				if restOfPath == '': restOfPath = "index.html"  #Again, should be configurable
				ssPath = os.path.join(basePath, restOfPath)
				ssPath = os.path.normpath(ssPath)

			extraPathInfo=''
			if not os.path.isdir(os.path.split(ssPath)[0]):
				while restOfPath != '':  #don't go too far
					if not os.path.isdir(os.path.join(basePath,os.path.split(restOfPath)[0])): #strip down to the first real directory
						restOfPath,extra = os.path.split(restOfPath)
						if extraPathInfo != '': #avoid a trailing os.sep
							extraPathInfo=os.path.join(extra,extraPathInfo)
						else: extraPathInfo=extra
					else: # if I get here, I'm either at the real Servlet, or I'm at basePath
						ssPath = os.path.join(basePath,restOfPath)
						urlPath = urlPath[:string.rindex(urlPath,extraPathInfo)-1]#remove trailing /
						break

			if os.path.splitext(ssPath)[1]=='':
				filenames = glob(ssPath+'.*')

				# Ignore files with extensions we don't care about
				ignoreExts = self.setting('ExtensionsToIgnore')
				for i in range(len(filenames)):
					if os.path.splitext(filenames[i])[1] in ignoreExts:
						filenames[i] = None
				filenames = filter(lambda filename: filename!=None, filenames)

				if len(filenames)==1:
					ssPath = filenames[0]
				else:
					print 'WARNING: For %s, got multiple filenames: %s' % (urlPath, filenames)
					return None  # that's right: return None and don't modify the cache
				
			self._serverSidePathCacheByPath[urlPath] = ssPath
			request._fields['extraPathInfo']=extraPathInfo
			
		return ssPath


def main(requestDict):
	"""
	Returns a raw reponse. This method is mostly used by OneShotAdaptor.py.
	"""
	from WebUtils.HTMLForException import HTMLForException
	try:
		fauxserver = Configurable()
		fauxserver.settings['ServerThreads']=1
		assert type(requestDict) is type({})
		from HTTPRequest import HTTPRequest
		request = HTTPRequest(requestDict)
		app = Application(useSessionSweeper=0,server=fauxserver)
		return app.dispatchRequest(request).response().rawResponse()
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

#!/usr/bin/env python

from Common import *
from UserDict import UserDict
from Object import Object
from types import FloatType, ClassType

from ExceptionHandler import ExceptionHandler  

from ConfigurableForServerSidePath import ConfigurableForServerSidePath

from TaskKit.Scheduler import Scheduler

from HTTPRequest import HTTPRequest
from Transaction import Transaction
from Session import Session
import URLParser
import HTTPExceptions

debug = 0

class EndResponse(Exception):
	"""
	Used to prematurely break out of the awake()/respond()/sleep()
	cycle without reporting a traceback.  During servlet
	processing, if this exception is caught during awake() or respond() 
	then sleep() is called and the response is sent.  If caught during
	sleep(), processing ends and the response is sent.
	"""
	pass

class Application(ConfigurableForServerSidePath, Object):
	"""
	`Application` and `AppServer` work together to setup up and
	dispatch requests.  The distinction between the two is largely
	historical, but AppServer communicates directly with Adapters
	(or speaks protocols like HTTP), and Application receives the
	(slightly) processed input from AppServer and turns it into
	`Transaction`, `HTTPRequest`, `HTTPResponse`, and `Session`.

	Application is a singleton, which belongs to the AppServer.
	You can get access through the Transaction object
	(``transaction.application()``), or you can do::

	    from AppServer import globalAppServer
	    application = AppServer.application()

	Settings for Application are taken from
	``Configs/Application.config``, and it is used for many
	global settings, even if they aren't closely tied to the
	Application object itself.
	"""

	## Init ##

	def __init__(self, server):
		"""
		Called only by `AppServer`, sets up the Application.
		"""

		self._server = server
		self._serverSidePath = server.serverSidePath()

		ConfigurableForServerSidePath.__init__(self)
		Object.__init__(self)

		if self.setting('PrintConfigAtStartUp'):
			self.printConfig()

		self.initVersions()

		self._shutDownHandlers = []

		## For TaskManager:
		if self._server.isPersistent():
			self._taskManager = Scheduler(1)
			self._taskManager.start()

		# For session store:
		from SessionMemoryStore import SessionMemoryStore
		from SessionFileStore import SessionFileStore
		from SessionDynamicStore import SessionDynamicStore
		klass = locals()['Session'
				 + self.setting('SessionStore','File')
				 + 'Store']
		assert type(klass) is ClassType
		self._sessions = klass(self)

		print 'Current directory:', os.getcwd()

		URLParser.initApp(self)
		self._rootURLParser = URLParser.ContextParser(self)

		self.running = 1

		self.startSessionSweeper()

		self._exceptionHandlerClass = ExceptionHandler

	def initVersions(self):
		"""
		Initialize attributes that store the Webware and
		WebKit versions as both tuples and strings. These are
		stored in the Properties.py files.
		"""
		from MiscUtils.PropertiesObject import PropertiesObject
		props = PropertiesObject(os.path.join(self.webwarePath(),
						      'Properties.py'))
		self._webwareVersion = props['version']
		self._webwareVersionString = props['versionString']

		props = PropertiesObject(os.path.join(self.webKitPath(),
						      'Properties.py'))
		self._webKitVersion = props['version']
		self._webKitVersionString = props['versionString']


	def taskManager(self):
		"""
		Accessor: `TaskKit.Scheduler` instance
		"""
		return self._taskManager

	def startSessionSweeper(self):
		"""
		Starts the session sweeper, `WebKit.Tasks.SessionTask`,
		which deletes session objects (and disk copies of those
		objects) that have expired.
		"""
		from Tasks import SessionTask
		import time
		task = SessionTask.SessionTask(self._sessions)
		tm = self.taskManager()
		sweepinterval = self.setting('SessionTimeout')*60/10
		tm.addPeriodicAction(time.time()+sweepinterval,
				     sweepinterval, task, "SessionSweeper")
		print "Session Sweeper started"

	def shutDown(self):
		"""
		Called by AppServer when it is shuting down.  The
		`__del__` function of Application probably won't be
		called due to circular references.
		"""
		print "Application is Shutting Down"
		self.running = 0
		if hasattr(self, '_sessSweepThread'):
			# We don't always have this, hence the 'if' above
			self._closeEvent.set()
			self._sessSweepThread.join()
			del self._sessSweepThread
		self._sessions.storeAllSessions()
		if self._server.isPersistent():
			self.taskManager().stop()
		del self._sessions
		del self._server

		# Call all registered shutdown handlers
		for shutDownHandler in self._shutDownHandlers:
			shutDownHandler()
		del self._shutDownHandlers

		print "Application has been succesfully shutdown."

	def addShutDownHandler(self, func):
		"""
		Functions added through `addShutDownHandler` will be
		called when the AppServer is shutting down.  You can use
		this hook to close database connections, clean up resources,
		save data to disk, etc.
		"""
		self._shutDownHandlers.append(func)

	## Config ##

	def defaultConfig(self):
		":ignore:"
		return {
			'PrintConfigAtStartUp': 1,
			'LogActivity':          1,
			'ActivityLogFilename':  'Logs/Activity.csv',
			'ActivityLogColumns':
			['request.remoteAddress', 'request.method',
			 'request.uri', 'response.size',
			 'servlet.name', 'request.timeStamp',
			 'transaction.duration',
			 'transaction.errorOccurred'],
			'SessionStore':         'Memory',  # can be File or Memory
			'SessionTimeout':        60,  # minutes
			'IgnoreInvalidSession': 1,
			'UseAutomaticPathSessions': 0,

			# Error handling
			'ShowDebugInfoOnErrors': 1,
			'IncludeFancyTraceback': 0,
			'FancyTracebackContext': 5,
			'UserErrorMessage':      'The site is having technical difficulties with this page. An error has been logged, and the problem will be fixed as soon as possible. Sorry!',
			'ErrorLogFilename':      'Logs/Errors.csv',
			'SaveErrorMessages':     1,
			'ErrorMessagesDir':      'ErrorMsgs',
			'EmailErrors':           0, # be sure to review the following settings when enabling error e-mails
			'ErrorEmailServer':      'mail.-.com',
			'ErrorEmailHeaders':     { 'From':         '-@-.com',
			                           'To':           ['-@-.com'],
			                           'Reply-to':     '-@-.com',
			                           'content-type': 'text/html',
			                           'Subject':      'Error'
			                         },
			'MaxValueLengthInExceptionReport': 500,
			'RPCExceptionReturn':    'traceback',
			'ReportRPCExceptionsInWebKit':   1,
			'Contexts':              { 'default':       'Examples',
			                           'Admin':         'Admin',
			                           'Examples':      'Examples',
			                           'Documentation': 'Documentation',
			                           'Testing':       'Testing',
			                         },
			'Debug':	{
				'Sessions': 0,
			},
			'OldStyleActions': 0,
		}

	def configFilename(self):
		":ignore:"
		return self.serverSidePath('Configs/Application.config')

	def configReplacementValues(self):
		":ignore:"
		return self._server.configReplacementValues()


	## Versions ##

	def version(self):
		"""
		Returns the version of the application. This
		implementation returns '0.1'. Subclasses should
		override to return the correct version number.
		"""
		## @@ 2000-05-01 ce: Maybe this could be a setting 'AppVersion'
		## @@ 2003-03 ib: Does anyone care about this?  What's this
		## version even supposed to mean?
		return '0.1'

	def webwareVersion(self):
		""" Returns the Webware version as a tuple. """
		return self._webwareVersion

	def webwareVersionString(self):
		""" Returns the Webware version as a printable string. """
		return self._webwareVersionString

	def webKitVersion(self):
		""" Returns the WebKit version as a tuple. """
		## @@ 2003-03 ib: This is synced with Webware now,
		## should be removed because redundant (and not that useful
		## anyway)
		return self._webKitVersion

	def webKitVersionString(self):
		""" Returns the WebKit version as a printable string. """
		return self._webKitVersionString


	## Sessions ##

	def session(self, sessionId, default=NoDefault):
		"""
		The session object for `sessionId`.  Raises
		``KeyError`` if session not found and no default
		is given.
		"""
		if default is NoDefault:
			return self._sessions[sessionId]
		else:
			return self._sessions.get(sessionId, default)

	def hasSession(self, sessionId):
		"""
		Does session `sessionId` exist.
		"""
		return self._sessions.has_key(sessionId)

	def sessions(self):
		"""
		A dictionary of all the session objects.
		"""
		return self._sessions

	def createSessionForTransaction(self, transaction):
		"""
		Gets the session object for the transaction -- if the
		session already exists, returns that, otherwise creates
		a new session.

		Finding the session ID is done in `Transaction.sessionId`.
		"""
		
		debug = self.setting('Debug').get('Sessions')
		if debug:
			prefix = '>> [session] createSessionForTransaction:'
		sessId = transaction.request().sessionId()
		if debug:
			print prefix, 'sessId =', sessId
		if sessId:
			try:
				session = self.session(sessId)
				if debug: print prefix, 'retrieved session =', session
			except KeyError:
				sessId = None
		if not sessId:
			session = Session(transaction)
			self._sessions[session.identifier()] = session
			if debug: print prefix, 'created session =', session
		transaction.setSession(session)
		return session


	## Misc Access ##

	def server(self):
		"""
		Acessor: the AppServer
		"""
		return self._server

	def serverSidePath(self, path=None):
		"""
		Returns the absolute server-side path of the WebKit
		application. If the optional path is passed in, then
		it is joined with the server side directory to form a
		path relative to the app server.
		"""
		if path:
			return os.path.normpath(
				os.path.join(self._serverSidePath, path))
		else:
			return self._serverSidePath

	def webwarePath(self):
		"""
		Path of the ``Webware/`` directory
		"""
		return self._server.webwarePath()

	def webKitPath(self):
		"""
		Path of the ``Webware/WebKit/`` directory
		"""
		return self._server.webKitPath()


	def name(self):
		"""
		Name by which this was started.  Usually ``AppServer``
		"""
		## @@ 2003-03 ib: unconfirmed
		return sys.argv[0]

	## Activity Log ##

	def writeActivityLog(self, transaction):
		"""
		Writes an entry to the script log file. Uses settings
		``ActivityLogFilename`` and ``ActivityLogColumns``.
		"""
		filename = self.serverSidePath(
			self.setting('ActivityLogFilename'))
		if os.path.exists(filename):
			file = open(filename, 'a')
		else:
			file = open(filename, 'w')
			file.write(','.join(self.setting('ActivityLogColumns'))+'\n')
		values = []
		# We use UserDict on the next line because we know it
		# inherits NamedValueAccess and reponds to
		# valueForName()
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
				value = '(unknown)'
			if type(value) is FloatType:
				# probably need more flexibility in
				# the future
				value = '%0.2f' % value
				
			else:
				value = str(value)
			values.append(value)
		file.write(','.join(values)+'\n')
		file.close()

		for i in objects.keys():
			objects[i] = None

	"""
	**Request Dispatching**

	These are the entry points from `AppServer`, which take
	a raw request, turn it into a transaction, run the transaction,
	and clean up.  

	"""

	def dispatchRawRequest(self, requestDict, strmOut):
		"""
		Dispatch a raw request, as passed from the Adapter
		through the AppServer.  This method creates the
		request, response, and transaction object, then runs
		(via `runTransaction`) the transaction.  It also
		catches any exceptions, which are then passed on to
		`handleExceptionInTransaction`.
		"""
		
		trans = None
		try:
			request = self.createRequestForDict(requestDict)
			trans = Transaction(application=self, request=request)
			request.setTransaction(trans)
			response = request.responseClass()(trans, strmOut)
			trans.setResponse(response)
			self.runTransaction(trans)
			trans.response().deliver()
		except:
			if trans:
				trans.setErrorOccurred(1)
			self.handleExceptionInTransaction(sys.exc_info(), trans)
			trans.response().deliver()
			
		if self.setting('LogActivity'):
			self.writeActivityLog(trans)
		request.clearTransaction()
		response.clearTransaction()
		return trans

	def createRequestForDict(self, requestDict):
		"""
		Create a request object (subclass of `Request`) given the
		raw dictionary as passed by the adapter.

		The class of the request may be based on the contents
		of the dictionary (though only `HTTPRequest` is
		currently created), and the request will later
		determine the class of the response.

		Called by `dispatchRawRequest`.
		"""
		
		format = requestDict['format']
		# Maybe an EmailAdapter would make a request with a
		# format of Email, and an EmailRequest would be
		# generated.  For now just CGI/HTTPRequest.
		assert format == 'CGI'
		return HTTPRequest(requestDict)

	def runTransaction(self, trans):
		"""
		Executes the transaction, handling HTTPException errors.
		Finds the servlet (using the root parser, probably
		`URLParser.ContextParser`, to find the servlet for the
		transaction, then calling `runServlet`.

		Called by `dispatchRawRequest`.
		"""

		servlet = None
		try:
			servlet = self._rootURLParser.findServletForTransaction(trans)
			self.runServlet(servlet, trans)
		except HTTPExceptions.HTTPException, err:
			err.setTransaction(trans)
			trans.response().displayError(err)
		except EndResponse:
			pass
		if servlet:
			# Return the servlet to its pool
			# 3-03 ib @@: what's this really supposed to do?
			self.returnServlet(servlet)

	def runServlet(self, servlet, trans):
		"""
		Executes the servlet using the transaction.  This is
		the `awake`/`respond`/`sleep` sequence of calls, or if the
		servlet supports it, a single `runTransaction` call
		(which is presumed to make the awake/respond/sleep calls
		on its own).  Using `runTransaction` allows the servlet
		to override the basic call sequence, or catch errors from
		that sequence.

		Called by `runTransaction`.
		"""
		
		if hasattr(servlet, 'runTransaction'):
			servlet.runTransaction(trans)
		else:
			# For backward compatibility (Servlet.runTransaction
			# implements this same sequence of calls, but
			# by keeping it in the servlet it's easier to
			# for the servlet to catch exceptions.
			try:
				servlet.awake(trans)
				servlet.respond(trans)
			finally:
				servlet.sleep(trans)
	
	def forward(self, trans, url, context=None):
		"""
		Forward the request to a different (internal) url.
		The transaction's URL is changed to point to the new
		servlet, and the transaction is simply run again.

		Output is _not_ accumulated, so if the original servlet
		had any output, the new output will _replace_ the old
		output.

		You can change the request in place to control the
		servlet you are forwarding to -- using methods like
		`HTTPRequest.setField`.

		@@ 2003-03 ib: how does the forwarded servlet knows
		that it's not the original servlet?
		"""
		
		# Reset the response to a "blank slate"
		trans.response().reset()
		
		# Include the other servlet
		self.includeURL(trans, url, context)
		
		# Raise an exception to end processing of this request
		raise EndResponse

	def callMethodOfServlet(self, trans, url, method, *args, **kw):
		"""
		Call a method of the servlet referred to by the url,
		potentially in a particular context (use the context
		keyword argument).  Calls sleep and awake before and
		after the method call.  Or, if the servlet defines it,
		then `runMethodForTransaction` is used (analogous to the
		use of `runTransaction` in `forward`).

		The entire process is similar to `forward`, except that
		instead of `respond`, `method` is called (`method` should
		be a string, ``*args`` and ``**kw`` are passed as
		arguments to that method).

		A `context` keyword argument (as used in `forward`)
		is also allowed, though it isn't present in the
		method signature.
		"""
		
		# 3-03 ib@@: Does anyone actually use this method?
		# 2003-04-08 jdh: I use callMethodOfServlet, but I don't use
		# this little context trick.  Not sure what you were referring to.  
		if kw.has_key('context'):
			context = kw['context']
			del kw['context']
		else:
			context = None
			
		urlPath = self.resolveInternalRelativePath(trans, url, context)
		req = trans.request()
		currentPath = req.urlPath()
		currentServlet = trans._servlet
		req.setURLPath(urlPath)
		req.addParent(currentServlet)
		
		servlet = self._rootURLParser.findServletForTransaction(trans)
		trans._servlet = servlet
		if hasattr(servlet, 'runMethodForTransaction'):
			result = servlet.runMethodForTransaction(trans, method, *args, **kw)
		else:
			servlet.awake(trans)
			result = getattr(servlet, method)(*args, **kw)
			servlet.sleep(trans)

		# Put things back
		req.setURLPath(currentPath)
		req.popParent()
		trans._servlet = currentServlet

		return result

	def includeURL(self, trans, url, context=None):
		"""
		Include the servlet given by the url, potentially in
		context (or current context).  Like `forward`, except
		control is ultimately returned to the servlet.
		"""
		
		urlPath = self.resolveInternalRelativePath(trans, url, context)
		req = trans.request()
		currentPath = req.urlPath()
		currentServlet = trans._servlet
		req.setURLPath(urlPath)
		req.addParent(currentServlet)

		servlet = self._rootURLParser.findServletForTransaction(trans)
		trans._servlet = servlet
		servlet.runTransaction(trans)
		req.setURLPath(currentPath)
		req.popParent()
		trans._servlet = currentServlet

	def resolveInternalRelativePath(self, trans, url, context=None):
		"""
		Given a URL and an optional context, return the absolute
		internal URL.  URLs are assumed relative to the current URL.

		Absolute paths are returned unchanged.
		"""
		req = trans.request()
		if not url.startswith('/'):
			origPath = req.urlPath()
			if origPath.endswith('/'):
				origDir = origPath
			else:
				origDir = os.path.dirname(origPath) + '/'
			return origDir + url
		else:
			if context is None:
				context = req._contextName
			return '/%s%s' % (context, url)
			
	def returnServlet(self, servlet):
		# @@: this should return the servlet to its factory
		pass

	def handleExceptionInTransaction(self, excInfo, transaction):
		"""
		Handles exception `excInfo` (as returned by
		``sys.exc_info()``) that was generated by `transaction`.
		It may display the exception report, email the report,
		etc., handled by `ExceptionHandler.ExceptionHandler`.
		"""
		req = transaction.request()
		editlink = req.adapterName() + "/Admin/EditFile"
		self._exceptionHandlerClass(self, transaction, excInfo,
						 {"editlink": editlink})

	def rootURLParser(self):
		"""
		Accessor: the Rool URL parser -- URL parsing (as defined
		by subclasses of `URLParser.URLParser`) starts here.
		Other parsers are called in turn by this parser.
		"""
		return self._rootURLParser

	def hasContext(self, name):
		"""
		Does context `name` exist?
		"""
		return self._rootURLParser._contexts.has_key(name)

	def addContext(self, name, path):
		"""
		Add a context by named `name`, rooted at `path`.
		This gets imported as a package, and the last directory
		of `path` does not have to match the context name.
		(The package will be named `name`, regardless of `path`).

		Delegated to `URLParser.ContextParser`.
		"""
		self._rootURLParser.addContext(name, path)

	def addServletFactory(self, factory):
		"""
		Adds a ServletFactory, delegated to the
		`URLParser.ServletFactoryManager` singleton.
		"""
		URLParser.ServletFactoryManager.addServletFactory(factory)

	def contexts(self):
		"""
		Returns a dictionary of context-name: context-path.
		"""
		return self._rootURLParser._contexts

	def writeExceptionReport(self, handler):
		# @@ 2003-02 ib: does anyone care?
		pass









def main(requestDict):
	"""
	Returns a raw reponse. This method is mostly used by
	OneShotAdapter.py.
	"""
	from WebUtils.HTMLForException import HTMLForException
	try:
		assert type(requestDict) is type({})
		app = Application(useSessionSweeper=0)
		return app.runRawRequest(requestDict).response().rawResponse()
	except:
		return {
			'headers': [('Content-type', 'text/html')],
			'contents': '<html><body>%s</html></body>' % HTMLForException()
		}


"""
You can run Application as a main script, in which case it expects a
single argument which is a file containing a dictionary representing
a request. This technique isn't very popular as Application itself
could raise exceptions that aren't caught. See `CGIAdapter` and
`AppServer` for a better example of how things should be done.

Largely historical.
"""
if __name__=='__main__':
	if len(sys.argv)!=2:
		sys.stderr.write('WebKit: Application: Expecting one filename argument.\n')
	requestDict = eval(open(sys.argv[1]).read())
	main(requestDict)

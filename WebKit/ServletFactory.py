from Common import *
from Servlet import Servlet
import sys
from types import ClassType


class ServletFactory(Object):
	'''
	ServletFactory is an abstract class that defines the protocol for all servlet factories.

	Servlet factories are used by the Application to create servlets for transactions.

	A factory must inherit from this class and override uniqueness(), extensions() and createServletForTransaction(). Do not invoke the base class methods as they all raise SubclassResponsibilityErrors.

	Each method is documented below.
	'''

	def __init__(self, application):
		''' Stores a reference to the application in self._app, because subclasses may or may not need to talk back to the application to do their work. '''
		Object.__init__(self)
		self._app = application

	def name(self):
		''' Returns the name of the factory. This is a convenience for the class name. '''
		return self.__class__.__name__

	def uniqueness(self):
		''' Returns a string to indicate the uniqueness of the ServletFactory's servlets. The Application needs to know if the servlets are unique per file, per extension or per application. Return values are 'file', 'extension' and 'application'.
			*** NOTE: Application only supports 'file' uniqueness at this point in time. '''
		raise SubclassResponsibilityError

	def extensions(self):
		''' Return a list of extensions that match this handler. Extensions should include the dot. An empty string indicates a file with no extension and is a valid value. The extension '.*' is a special case that is looked for a URL's extension doesn't match anything. '''
		raise SubclassResponsibilityError

	def createServletForTransaction(self, transaction):
		''' Returns a new servlet that will handle the transaction. This method should do no caching (e.g., it should really create the servlet upon each invocation) since caching is already done at the Application level. '''
		raise SubclassResponsibilityError


class PythonServletFactory(ServletFactory):
	'''
	This is the factory for ordinary, Python servlets whose extensions are empty or .py. The servlets are unique per file since the file itself defines the servlet.
	'''

	def __init__(self,app):
		ServletFactory.__init__(self,app)
		self._cache = {}

	def uniqueness(self):
		return 'file'

	def extensions(self):
		return ['', '.py']

	def old_servletForTransaction(self, transaction):
		path = transaction.request().serverSidePath()
		globals = {}
		execfile(path, globals)
		from types import ClassType
		name = os.path.splitext(os.path.split(path)[1])[0]
		assert globals.has_key(name), 'Cannot find expected servlet class named "%s".' % name
		theClass = globals[name]
		assert type(theClass) is ClassType
		assert issubclass(theClass, Servlet)
		return theClass()

	def servletForTransaction(self, transaction):
		path = transaction.request().serverSidePath()
		name = os.path.splitext(os.path.split(path)[1])[0]
		if not self._cache.has_key(path):
			self._cache[path] = {}
		if os.path.getmtime(path)>self._cache[path].get('mtime',0):
			globals = {}
			execfile(path, globals)
			assert globals.has_key(name), 'Cannot find expected servlet class named %s in %s.' % (repr(name), repr(path))
			theClass = globals[name]
			assert type(theClass) is ClassType
			assert issubclass(theClass, Servlet)
			self._cache[path]['mtime'] = os.path.getmtime(path)
			self._cache[path]['class'] = theClass
		else:
			theClass = self._cache[path]['class']
		return theClass()

	def import_servletForTransaction(self, transaction):
		path = transaction.request().serverSidePath()
		name = os.path.splitext(os.path.split(path)[1])[0]
		if not self.cache.has_key(name): self.cache[name]={}
		if os.path.getmtime(path) > self.cache[name].get('mtime',0):
			if not os.path.split(path)[0] in sys.path: sys.path.append(os.path.split(path[0]))
			module_obj=__import__(name)
			reload(module_obj)#force reload
			inst =  module_obj.__dict__[name]()
			self.cache[name]['mtime']=os.path.getmtime(path)
		else:
			inst = sys.modules[name].__dict__[name]()
		return inst


class UnknownFileTypeServletFactory(ServletFactory):
	'''
	This is the factory for files of an unknown type (e.g., not .py, not .psp, etc.).

	The servlet returned will simply redirect the client to a URL that does not include
	the adaptor's filename.
	'''

	def uniqueness(self):
		return 'file' # should really be 'application', but that's not supported yet.

	def extensions(self):
		return ['.*']

	def servletForTransaction(self, transaction):
		path = transaction.request().serverSidePath()
		servlet = UnknownFileTypeServlet(path=path)

		# @@ 2000-05-08 ce: the following is horribly CGI specific and hacky
		env = transaction.request()._environ
		newURL = os.path.split(env['SCRIPT_NAME'])[0] + env['PATH_INFO']

		servlet.setLocation(newURL)
		return servlet


from HTTPServlet import HTTPServlet
class UnknownFileTypeServlet(HTTPServlet):
	def setLocation(self, location):
		self._location = location

	def respondToGet(self, trans):
		trans.response().sendRedirect(self._location)

	def respondToPost(self, trans):
		# @@ 2000-05-08 ce: Does a redirect make sense for a POST?
		trans.response().sendRedirect(self._location)

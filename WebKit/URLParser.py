import WebKit.ImportSpy as imp
import re, os, sys
from MiscUtils.ParamFactory import ParamFactory
import warnings
from WebKit.HTTPExceptions import *
import AppServer

# Legal characters for use in a module name -- used when turning
# an entire path into a module name.
moduleNameRE = re.compile('[^a-zA-Z_]')

def application():
	return AppServer.globalAppServer.application()

class URLParser:

	"""
	URLParser is the base class for all URL parsers.  Though
	its functionality is sparse, it may be expanded in the future.
	Subclasses should implement a `parse` method, and may also
	want to implement an `__init__` method with arguments that
	control how the parser works (for instance, passing a starting
	path for the parser)
	"""

	def __init__(self):
		pass

	def findServletForTransaction(self, trans):
		return self.parse(trans, trans.request().urlPath())

class ContextParser(URLParser):

	"""
	ContextParser uses the Application.config context settings
	to find the context of the request.  It then passes the
	request to a FileParser rooted in the context path.

	The context is the first element of the URL, or if no context
	matches that then it is the ``default`` context (and the
	entire URL is passed to the default context's FileParser).
	"""

	def __init__(self, app):
		"""
		ContextParser is usually created by Application, which
		passes all requests to it.

		In __init__ we take the ``Contexts`` setting from
		Application.config and parse it slightly.
		"""
		
		URLParser.__init__(self)
		# self._context will be a dictionary of context
		# names and context directories.  It is set by
		# `addContext`.
		self._contexts = {}
		
		contexts = app.setting('Contexts')
		contextDirs = {}

		# Figure out what the default context is:
		for name, path in contexts.items():
			if name != 'default':
				contextDirs[self.absContextPath(path)] = name

		if contexts.has_key('default'):
			if contexts.has_key(contexts['default']):
				# The default context refers to another context,
				# not a unique context
				self._defaultContext = contexts['default']
				del contexts['default']
				
			elif contextDirs.has_key(self.absContextPath(contexts['default'])):
				# The default context has the same directory
				# as another context, so it's still not unique
				self._defaultContext = contextDirs[self.absContextPath(contexts['default'])]
				del contexts['default']
			else:
				# The default context has no other name
				self._defaultContext = 'default'
		else:
			# Examples is a last-case default context, otherwise
			# use a context that isn't built into Webware as
			# the default
			self._defaultContext = 'Examples'
			for name in contexts.keys():
				if name not in ('Admin', 'Examples', 'Docs', 'Testing'):
					self._defaultContext = name
					break

		for name, dir in contexts.items():
			self.addContext(name, dir)

	def addContext(self, name, dir):
		"""
		Add a context to the system.  The context will be
		imported as a package, going by `name`, from the
		given directory.  The directory doesn't have to
		match the context name.
		"""
		
		try:
			importAsName = name
			localDir, packageName = os.path.split(dir)
			if sys.modules.has_key(importAsName):
				mod = sys.modules[importAsName]
			else:
				res = imp.find_module(packageName, [localDir])
				mod = imp.load_module(name, *res)
		except ImportError, e:
			print 'Error loading context: %s: %s: dir=%s' \
			      % (name, e, dir)
			return

		if hasattr(mod, 'contextInitialize'):
			result = mod.contextInitialize(self, os.path.normpath(os.path.join(os.getcwd(), dir)))
			# @@: funny hack...?
			if result != None and result.has_key('ContentLocation'):
				dir = result['ContentLocation']

		print 'Loading context: %s at %s' % (name, dir)
		self._contexts[name] = dir

	def absContextPath(self, path):
		if os.path.isabs(path):
			return path
		else:
			return application().serverSidePath(path)

	def parse(self, trans, requestPath):
		"""
		Get the context name, and dispatch to a FileParser
		rooted in the context's path.
		"""
		# This is a hack... this should probably go in the
		# Transaction class:
		trans._fileParserInitSeen = {}
		if not requestPath:
			raise HTTPMovedPermanently(webkitLocation='/')
		parts = requestPath[1:].split('/', 1)
		if len(parts) == 1:
			rest = ''
		else:
			rest = '/' + parts[1]
		contextName = parts[0]

		if not self._contexts.has_key(contextName):
			contextName = self._defaultContext
			rest = requestPath
		trans.request()._serverSideContextPath = self._contexts[contextName]
		trans.request()._contextName = contextName
		fpp = FileParser(self._contexts[contextName])
		return fpp.parse(trans, rest)
		
class _FileParser(URLParser):
	"""
	FileParser dispatches to servlets in the filesystem, as well
	as providing hooks to override the FileParser.

	FileParser objects are threadsafe.  A factory function is
	used to cache FileParser instances, so for any one path only
	a single FileParser instance will exist.
	"""

	def __init__(self, path):
		URLParser.__init__(self)
		self._path = path
		self._initModule = None

	def parse(self, trans, requestPath):
		"""
		Return the servlet.  __init__ files will be used for various
		hooks (see parseInit for more)
		"""

		# print "FP(%r) parses %r" % (self._path, requestPath)

		result = self.parseInit(trans, requestPath)
		if result is not None:
			return result
			
		assert not requestPath or requestPath.startswith('/'), \
		       "Not what I expected: %s" % repr(requestPath)
		if not requestPath or requestPath == '/':
			return self.parseIndex(trans, requestPath)
		
		parts = requestPath[1:].split('/', 1)
		nextPart = parts[0]
		if len(parts) > 1:
			restPart = '/' + parts[1]
		else:
			restPart = ''

		names = self.filenamesForBaseName(os.path.join(self._path, nextPart))

		if len(names) > 1:
			warnings.warn("More than one file matches %s in %s: %s"
						  % (requestPath, self._path, names))
			# @@: add info
			raise HTTPNotFound
		elif not names:
			return self.parseIndex(trans, requestPath)

		name = names[0]
		if os.path.isdir(name):
			# directories are dispatched to FileParsers rooted
			# in that directory
			fpp = FileParser(os.path.join(self._path, name))
			return fpp.parse(trans, restPart)

		trans.request()._extraURLPath = restPart
		trans.request()._serverSidePath = os.path.join(self._path, name)
		return ServletFactoryManager.servletForFile(trans, os.path.join(self._path, name))


	_filesSetup = 0
				
	def filenamesForBaseName(self, baseName):
		"""
		Given a path, like ``/a/b/c``, searches for files in ``/a/b``
		that start with ``c``.  The final name may include an extension,
		which is less ambiguous; though if you ask for file.html,
		and file.html.py exists, that file will be returned.

		If more than one file is returned for the basename, you'll
		get a 404.

		Some settings are used to control this.  All settings are
		in ``Application.config``:

		FilesToHide:
		    These files will be ignored, and even given a full
		    extension will not be used.  Takes a glob.
		FilesToServe:
		    If set, *only* files matching these globs will be
		    served, all other files will be ignored.
		ExtensionsToIgnore:
		    Files with these extensions will be ignored, but if a
		    complete filename (with extension) is given the file
		    *will* be served (unlike FilesToHide).  Extensions are
		    in the form ``".py"``
		ExtensionsToServe:
		    If set, only files with these extensions will be
		    served.  Like FilesToServe, only doesn't use globs.
		UseCascadingExtensions:
		    If true, then extensions will be prioritized.  So if
		    extension ``.tmpl`` shows up in ExtensionCascadeOrder
		    before ``.html``, then even if filenames with both
		    extensions exist, only the .tmpl file will be returned.
		ExtensionCascadeOrder:
		    A list of extensions, ordered by priority.
		"""

		if baseName.find('*') != -1:
			return []

		fileStart = os.path.basename(baseName)
		dir = os.path.dirname(baseName)
		filenames = []
		for filename in os.listdir(dir):
			if filename == fileStart:
				filenames.append(os.path.join(dir, filename))
			elif filename.startswith(fileStart) \
			     and os.path.splitext(filename)[0] == fileStart:
				filenames.append(os.path.join(dir, filename))
		good = []

		# Here's where all the settings (except cascading) come
		# into play -- we filter the possible files based on settings
		# here:
		for filename in filenames:
			ext = os.path.splitext(filename)[1]
			shortFilename = os.path.basename(filename)

			if ext in self._toIgnore and filename != baseName:
				continue
			if self._toServe and ext not in self._toServe:
				continue
			shouldServe = 1
			for regex in self._filesToHideRegexes:
				if regex.match(shortFilename):
					shouldServe = 0
					break
			if not shouldServe:
				continue
			if self._filesToServeRegexes:
				shouldServe = 0
				for regex in self._filesToServeRegexes:
					if regex.match(shortFilename):
						shouldServe = 1
						break
				if not shouldServe:
					continue
			good.append(filename)

		if self._useCascading and len(good) > 1:
			actualExtension = os.path.splitext(baseName)[1]
			for extension in self._cascadeOrder:
				if baseName + extension in good \
				   or extension == actualExtension:
					return [baseName + extension]

		return good

	def parseIndex(self, trans, requestPath):
		"""
		Return the servlet for a directory index (i.e., ``Main`` or
		``index``).
		"""

		# if requestPath is empty, then we're missing the trailing /
		if not requestPath:
			raise HTTPMovedPermanently(webkitLocation=trans.request().urlPath() + "/")
		if requestPath == '/':
			requestPath = ''
		for directoryFile in self._directoryFile:
			names = self.filenamesForBaseName(
				os.path.join(self._path, directoryFile))
			if len(names) > 1:
				warnings.warn("More than one file matches the index file %s in %s: %s"
					      % (directoryFile, self._path, names))
				raise HTTPNotFound
			elif names:
				trans.request()._serverSidePath = os.path.join(self._path, names[0])
				trans.request()._extraURLPath = requestPath
				return ServletFactoryManager.servletForFile(trans, os.path.join(self._path, names[0]))
		# @@: add correct information here
		raise HTTPNotFound

	def initModule(self):
		"""
		Get the __init__ module object for this FileParser's
		directory.
		"""
		
		try:
			result = imp.find_module('__init__', [self._path])
			if result is None:
				return None
			file, initPath, desc = result
			fullName = moduleNameRE.sub('_', os.path.join(self._path, '__init__'))
			if len(fullName) > 100:
				fullName = fullName[:-50]
			module = None
			try:
				module = imp.load_module(fullName, file, initPath, desc)
			except:
				pass
			file.close()
			return module
		except ImportError:
			return None

	def parseInit(self, trans, requestPath):
		"""
		Parse the __init__ file, returning the resulting servlet,
		or None if no __init__ hooks were found.

		Hooks are put in by defining special functions or objects
		in your __init__, with specific names:

		`urlTransactionHook`:
		    A function that takes one argument (the transaction).
		    The return value from the function is ignored.  You
		    can modify the transaction with this function, though.

		`urlRedirect`:
		    A dictionary.  Keys in the dictionary are source
		    URLs, the value is the path to redirect to, or a
		    `URLParser` object to which the transaction should
		    be delegated.

		    For example, if the URL is ``/a/b/c``, and we've already
		    parsed ``/a`` and are looking for ``b/c``, and we fine
		    `urlRedirect`` in a.__init__, then we'll look for a key
		    ``b`` in the dictionary.  The value will be a directory
		    we should continue to (say, ``/destpath/``).  We'll
		    then look for ``c`` in ``destpath``.

		    If a key '' (empty string) is in the dictionary, then
		    if no more specific key is found all requests will
		    be redirected to that path.

		    Instead of a string giving a path to redirect to, you
		    can also give a URLParser object, so that some portions
		    of the path are delegated to different parsers.

		    If no matching key is found, and there is no '' key,
		    then parsing goes on as usual.

		`SubParser`:
		    This should be a class object.  It will be instantiated,
		    and then `parse` will be called with it, delegating to
		    this instance.  When instantiated, it will be passed
		    *this* FileParser instance; the parser can use this to
		    return control back to the FileParser after doing whatever
		    it wants to do.  

		    You may want to use a line like this to handle the names::

		        from ParserX import ParserX as SubParser

		`urlParser`:
		    This should be an already instantiated URLParser-like
		    object.  `parse(trans, requestPath)` will be called
		    on this instance.

		`urlParserHook`:
		    Like `urlParser`, except the method
		    `parseHook(trans, requestPath, fileParser)` will
		    be called, where fileParser is this FileParser instance.

		`urlJoins`:
		    Either a single path, or a list of paths.  You can also
		    use URLParser objects, like with `urlRedirect`.

		    Each of these paths (or parsers) will be tried in
		    order.  If it raises HTTPNotFound, then the next path
		    will be tried, ending with the current path.

		    Paths are relative to the current directory.  If you
		    don't want the current directory to be a last resort,
		    you can include '.' in the joins.
		"""

		if self._initModule is None:
			self._initModule = self.initModule()
		mod = self._initModule

		seen = trans._fileParserInitSeen.setdefault(self._path, {})
		
		if not seen.has_key('urlTransactionHook') \
		       and hasattr(mod, 'urlTransactionHook'):
			seen['urlTransactionHook'] = 1
			mod.urlTransactionHook(trans)

		if not seen.has_key('urlRedirect') \
		       and hasattr(mod, 'urlRedirect'):
			# @@: do we need this shortcircuit?
			seen['urlRedirect'] = 1
			try:
				nextPart, restPath = requestPath[1:].split('/', 1)
				restPath = '/' + restPath
			except ValueError:
				nextPart = requestPath[1:]
				restPath = ''
			if mod.urlRedirect.has_key(nextPart):
				redirTo = mod.urlRedirect[nextPart]
				redirPath = restPath
			elif mod.urlRedirect.has_key(''):
				redirTo = mod.urlRedirect['']
				redirPath = requestPath
			else:
				redirTo = None
			if redirTo:
				if type(redirTo) is type(""):
					fpp = FileParser(os.path.join(self._path, redirTo))
				else:
					fpp = redirTo
				return fpp.parse(trans, redirPath)

		if not seen.has_key('SubParser') \
		       and hasattr(mod, 'SubParser'):
			seen['SubParser'] = 1
			pp = mod.SubParser(self)
			return pp.parse(trans, requestPath)

		if not seen.has_key('urlParser') \
		       and hasattr(mod, 'urlParser'):
			seen['urlParser'] = 1
			pp = mod.urlParser
			return pp.parse(trans, requestPath)

		if not seen.has_key('urlParserHook') \
		       and hasattr(mod, 'urlParserHook'):
			seen['urlParserHook'] = 1
			pp = mod.urlParserHook
			return pp.parseHook(trans, requestPath, self)

		if not seen.has_key('urlJoins') \
		       and hasattr(mod, 'urlJoins'):
			seen['urlJoins'] = 1
			joinPath = mod.urlJoins
			if type(joinPath) is type(""):
				joinPath = [joinPath]
			for path in joinPath:
				path = os.path.join(self._path, path)
				if type(path) is type(""):
					parser = FileParser(os.path.join(self._path, path))
				else:
					parser = path
				try:
					return parser.parse(trans, requestPath)
				except HTTPNotFound:
					pass

		return None

FileParser = ParamFactory(_FileParser)	

class URLParameterParser(URLParser):
	"""
	Strips named parameters out of the URL, e.g. ``/path/SID=123/etc`` --
	the ``SID=123`` will be removed from the URL, and a field
	will be set in the request (so long as no field by that name
	already exists -- if a field does exist the variable is thrown
	away).

	It should be put in an __init__, like::

	    from WebKit.URLParser import URLParameterParser
	    urlParserHook = URLParameterParser()

	Or (slightly less efficient):

	    from WebKit.URLParser import URLParameterParser as SubParser
	"""

	def __init__(self, fileParser=None):
		self.fileParser = fileParser

	def parse(self, trans, requestPath):
		return self.parseHook(trans, requestPath, self.fileParser)

	def parseHook(self, trans, requestPath, hook):
		parts = requestPath.split('/')
		result = []
		req = trans.request()
		for part in parts:
			if part.find('=') != -1:
				name, value = part.split('=', 1)
				if not req.hasField(name):
					req.setField(name, value)
			else:
				result.append(part)
		return hook.parse(trans, '/'.join(result))

class ServletFactoryManagerClass:

	"""
	This singleton class manages all the servlet factories
	that are installed.  The primary instance is called
	ServletFactoryManager.

	Servlets can add themselves with the `addServletFactory(factory)`
	method; the factory must have an `extensions` method, which
	should return a list of extensions that the factory handles
	(like ``['.ht']``).  The special extension ``.*`` will match
	any file if no other factory is found.

	The method `servetForFile(trans, path)` will create a servlet
	based on the path, raising HTTPNotFound if no appropriate
	factory can be found.
	"""

	def __init__(self):
		self._factories = []
		self._factoryExtensions = {}

	def addServletFactory(self, factory):
		self._factories.append(factory)
		for ext in factory.extensions():
			assert not self._factoryExtensions.has_key(ext), \
				   "Extension %s for factory %s was already used by factory %s" \
				   % (repr(ext), factory.__name__,
					  self._factoryExtensions[ext].__name__)
			self._factoryExtensions[ext] = factory

	def factoryForFile(self, path):
		name, ext = os.path.splitext(path)
		if self._factoryExtensions.has_key(ext):
			return self._factoryExtensions[ext]
		if self._factoryExtensions.has_key('.*'):
			return self._factoryExtensions['.*']
		raise HTTPNotFound

	def servletForFile(self, trans, path):
		factory = self.factoryForFile(path)
		return factory.servletForTransaction(trans)

ServletFactoryManager = ServletFactoryManagerClass()

def initApp(app):
	"""
	Installs the propert servlet factories, and gets some
	settings from Application.config.

	We don't run this at the module level (using application())
	because the application hasn't been set up when this module
	is first imported.
	"""
	
	from UnknownFileTypeServlet import UnknownFileTypeServletFactory
	from ServletFactory import PythonServletFactory
	for factory in [UnknownFileTypeServletFactory, PythonServletFactory]:
		ServletFactoryManager.addServletFactory(factory(app))

	cls = _FileParser
	cls._filesToHideRegexes = []
	cls._filesToServeRegexes = []
	from fnmatch import translate as fnTranslate
	import re
	for pattern in app.setting('FilesToHide'):
		cls._filesToHideRegexes.append(
			re.compile(fnTranslate(pattern)))
	for pattern in app.setting('FilesToServe'):
		cls._filesToServeRegexes.append(
			re.compile(fnTranslate(pattern)))
	cls._toIgnore = app.setting('ExtensionsToIgnore')
	cls._toServe = app.setting('ExtensionsToServe')
	cls._useCascading = app.setting('UseCascadingExtensions')
	cls._cascadeOrder = app.setting('ExtensionCascadeOrder')
	cls._filesSetup = 1
	cls._directoryFile = app.setting('DirectoryFile')



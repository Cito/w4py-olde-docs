from Common import *


class PlugInError(Exception):
	pass


class PlugIn(Object):
	'''
	A plug-in is a software component that is loaded by WebKit in order to provide additional WebKit functionality without necessarily having to modify WebKit's source.
	The most infamous plug-in is PSP (Python Server Pages) which ships with Webware.
	Plug-ins often provide additional servlet factories, servlet subclasses, examples and documentation. Ultimately, it is the plug-in author's choice as to what to provide and in what manner.
	Instances of this class represent plug-ins which are ultimately Python packages (see the Python Tutorial, 6.4: "Packages" at http://www.python.org/doc/current/tut/node8.html#SECTION008400000000000000000).
	The plug-in/package must have an __init__.py while must contain a function:
		def InstallInWebKit(appServer):
	This function is invoked to take whatever actions are needed to plug the new component into WebKit. See PSP for an example.
	The plug-in is also required to declare __version__ (as in __version__ = 0.1).
	If you ask an AppServer for its plugIns(), you will get a list of instances of this class.
	The path of the plug-in is added to sys.path, if it's not already there. This is convenient, but we may need a more sophisticated solution in the future to avoid name collisions between plug-ins.
	Note that this class is hardly ever subclassed. The software in the plug-in package is what provides new functionality and there is currently no way to tell AppServer to use custom subclasses of this class on a case-by-case basis (and so far there is currently no need).

	Instructions for invoking:
		p = PlugIn(self, '../Foo')   # 'self' is typically AppServer. It gets passed to InstallInWebKit()
		p.load()
		p.install()
		# Note that load() and install() could easily raise exceptions. You should expect this.
	'''


	## Init, load and install ##

	def __init__(self, appServer, path):
		''' Initializes the plug-in with basic information. This lightweight constructor does not access the file system. '''
		self._appServer = appServer
		self._path = path
		self._dir, self._name = os.path.split(path)
		self._ver = '(unknown)'

	def load(self):
		''' Loads the plug-in into memory, but does not yet install it. '''
		print 'Loading plug-in: %s at %s' % (self._name, self._path)

		assert os.path.exists(self._path)

		# Update sys.path
		if not self._dir in sys.path:
			sys.path.append(self._dir)

		# Import the package
		self._module = __import__(self._name, globals(), [], [])

		# Inspect it and verify some required conventions
		if not hasattr(self._module, '__version__'):
			raise PlugInError, "Plug-in '%s' in '%s' has no __version__." % (self._name, self._dir)
		self._ver = self._module.__version__
		if not hasattr(self._module, 'InstallInWebKit'):
			raise PlugInError, "Plug-in '%s' in '%s' has no InstallInWebKit() function." % (self._name, self._dir)

	def install(self):
		''' Installs the plug-in by invoking it's required InstallInWebKit() function. '''
		self._module.InstallInWebKit(self._appServer)


	## Access ##

	def name(self):
		""" Returns the name of the plug-in. Example: 'Foo' """
		return self._name

	def version(self):
		""" Returns the version of the plug-in as reported in __version__ of the __init__.py of the plug-in package. Example: 0.2 """
		return self._ver

	def directory(self):
		""" Returns the directory in which the plug-in resides. Example: '..' """
		return self._dir

	def path(self):
		""" Returns the full path of the plug-in. Example: '../Foo' """
		return self._path

	def module(self):
		''' Returns the Python module object of the plug-in. '''
		return self._module

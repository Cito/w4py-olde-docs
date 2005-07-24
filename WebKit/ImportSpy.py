import ihooks
import os
import sys
import imp

"""
NO DOCS - this can all be more easily implemented by looking at
sys.modules, along with select files (like config files).  It's fast
to poll sys.modules, then we don't need this fanciness.

jdh: I'm not sure.  The original implementation from Tavis used sys.modules
like you say.  I implemented this to avoid having any polling at all,
but perhaps it's not worth it.  I'm not sure if there were other
factors in the design which pointed to this solution.


This module helps save the filepath of every module which is imported.
This is used by the `AutoReloadingAppServer` (see doc strings for more
information) to restart the server if any source files change.

Other than keeping track of the filepaths, the behaviour of this module
loader is identical to Python's default behaviour.

It will intercept normal imports, and can be used as a replacement for
the builtin `imp` module, most easily like::

    import ImportSpy as imp

The functions `load_module` and `find_module` act like their equivalents
in the `imp` module, and you may use the `watchFile(filename)` function
to add more files to watch without importing them (configuration files,
for instance).

.. inline:: load_module
.. inline:: find_module
.. inline:: watchFile
"""

True, False = 1==1, 0==1

try:
	set
except NameError:
	from sets import Set as set


class ImportLock:
	"""
	Provides a lock for protecting against concurrent imports.
	This is necessary because WebKit is multithreaded and uses its
	own import hook.
	
	This class abstracts the difference between using the Python
	interpreter's global import lock, and using our own RLock.
	The global lock is the correct solution, but is only available
	in recent Python versions (2.3 or 2.2.3).  If it's not
	available, we fall back to using an RLock (which is not as
	good, but better than nothing).
	"""

	def __init__(self):
		"""
		Aliases the `acquire` and `release` methods to
		`imp.acquire_lock` and `imp.release_lock` (if
		available), or to acquire and release our own RLock.
		"""
		if hasattr(imp,'acquire_lock'):
			self.acquire = imp.acquire_lock
			self.release = imp.release_lock
		else:
			from threading import RLock
			self._lock = RLock()
			self.acquire = self._lock.acquire
			self.release = self._lock.release

class ModuleLoader(ihooks.ModuleLoader):
	"""
	Implements the ihook module loader that tracks imported
	modules.  
	"""

	def __init__(self):
		assert modloader is None, \
		       "ModuleLoader can only be instantiated once"
		ihooks.ModuleLoader.__init__(self)
		self._fileList = {}
		self._notifyHook = None
		self._installed = False
		self._lock = ImportLock()
		self._modulesSet = set()

	def load_module(self,name,stuff):
		try:
			try:
				self._lock.acquire()
				mod = ihooks.ModuleLoader.load_module(self, name, stuff)
			finally:
				self._lock.release()
			self.recordFileName(stuff, mod)
		except:
			self.recordFileName(stuff, None)
			raise
		return mod

	def recordModules(self, moduleNames):
		for name in moduleNames:
			mod = sys.modules[name]
			if not hasattr(mod, '__file__'):
				# If we can't find it, we can't monitor it
				continue
			file = mod.__file__
			pathname = os.path.dirname(file)
			desc = None
			self.recordFileName((file, pathname, desc),
					    sys.modules[name])

	def fileList(self):
		return self._fileList

	def notifyOfNewFiles(self, hook):
		""" Called by someone else to register that they'd like to 
		be know when a new file is imported """
		self._notifyHook = hook

	def watchFile(self, filepath, getmtime=os.path.getmtime):
		modtime = getmtime(filepath)
		self._fileList[filepath] = modtime
		# send notification that this file was imported 
		if self._notifyHook:
			self._notifyHook(filepath,modtime)

	def recordFileName(self, stuff, mod, isfile=os.path.isfile):
		file, pathname, desc = stuff

		fileList = self._fileList
		if mod:
			assert sys.modules.has_key(mod.__name__)
			self._modulesSet.add(mod)
			
			# __orig_file__ is used for cheetah and psp mods; we want 
			# to record the source filenames, not the auto-generated modules
			f2 = getattr(mod, '__orig_file__', 0) 
			f = getattr(mod, '__file__', 0)

			if f2 and f2 not in fileList.keys():
				try:
					if isfile(f2):
						self.watchFile(f2)
				except OSError:
					pass
			elif f and f not in fileList.keys():
				# record the .py file corresponding to each '.pyc'
				if f[-4:].lower() in ['.pyc', '.pyo']:
					f = f[:-1]
				try:
					if isfile(f):
						self.watchFile(f)
					else:
						self.watchFile(os.path.join(f, '__init__.py'))
				except OSError:
					pass

		# also record filepaths which weren't successfully
		# loaded, which may happen due to a syntax error in a
		# servlet, because we also want to know when such a
		# file is modified
		elif pathname:
			if isfile(pathname):
				self.watchFile(pathname)

	def activate(self):
		imp = ihooks.ModuleImporter(loader=modloader)
		ihooks.install(imp)
		self.recordModules(sys.modules.keys())
		self._installed = True

	def delModules(self, includePythonModules=False, excludePrefixes=[]):
		"""
		Deletes all the modules that the ImportSpy has ever imported unless they
		are part of WebKit. This in support of DebugAppServer's useful (yet
		imperfect) support for AutoReload.
		"""
		for mod in self._modulesSet:
			name = mod.__name__
			if not includePythonModules and (not hasattr(mod, '__file__') or mod.__file__.startswith(sys.prefix)):
				continue
			exclude = False
			for prefix in excludePrefixes:
				if mod.__name__.startswith(prefix):
					exclude = True
					break
			if exclude:
				continue
			del sys.modules[mod.__name__]
		self._modulesSet = set()


# We do this little double-assignment trick to make sure ModuleLoader
# is only instantiated once.
modloader = None
modloader = ModuleLoader()

def reset():
	global modloader
	modloader = None
	modloader = ModuleLoader()


def load_module(name, file, filename, description):
	"""
	.. inline:: ModuleLoader.load_module
	"""
	return modloader.load_module(name,(file,filename,description))

def find_module(name,path=None):
	"""
	.. inline:: ModuleLoader.find_module
	"""
	return modloader.find_module(name,path)

def watchFile(*args):
	"""
	.. inline:: ModuleLoader.watchFile
	"""
	return modloader.watchFile(*args)


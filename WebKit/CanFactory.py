
import os
import imp
import sys

class CanFactory:
	"""Creates Cans on demand.  Looks only in the Cans directories.
	Unfortunately, this is a nasty hack, at least as far as directories are concerned.  The situation is that
	we want to be able to store Cans in he session object.  Session objects can be stored in files via pickling.
	When they are unpickled, the class module must be in sys.path.  The solution to this is custom importing,
	and apparently no one has time to get to that.
	"""
	def __init__(self, app):
		self._canClasses={}
		self._app = app
	    #self.__CanDir = app.getCanDir()
		self._canDirs=app._canDirs
		for i in self._canDirs:
			if not i in sys.path:
				sys.path.append(i)

	def addCanDir(self, newdir):
		self._canDirs.append(newdir)
		sys.path.append(newdir)


	def createCan(self, canName, *args, **kwargs):
		##Looks in the directories specified in the application.canDirs List
		self._canDirs = self._app._canDirs
		if self._canClasses.has_key(canName):
			klass = self._canClasses[canName]
		else:
			self.canDirs = self._app._canDirs
			res = imp.find_module(canName,self._canDirs)
			mod = imp.load_module(canName, res[0], res[1], res[2])
			klass = mod.__dict__[canName]
			self._canClasses[canName]=klass
		
		if len(args)==0 and len(kwargs)==0:
			instance = klass()
		elif len(args)==0:
			instance = apply(klass,kwargs)
		elif len(kwargs)==0:
			instance = apply(klass,args)
		else:
			instance = apply(klass,args,kwargs)
		return instance
	

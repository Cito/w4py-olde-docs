
import os
import imp

class CanFactory:
	"""Creates Cans on demand.  Looks only in the Cans directorys."""
	def __init__(self, app):
		self._canClasses={}
		self._app = app
	    #self.__CanDir = app.getCanDir()
		self._canDirs=app._canDirs

	def _createCan(self,canName,*args,**kargs):
		##Old version, only looks in one directory
		if self.__CanClasses.has_key(canName):
			klass=self.__CanClasses[canName]
		else:
			fullpath = os.path.join(self.__CanDir,canName+'.py')
			if not os.path.exists(fullpath):
				raise "CanNotFound"
			globals={}
			execfile(fullpath,globals)
			assert globals.has_key(canName)
			klass = self.__CanClasses[canName] = globals[canName]

		if len(args)==0 and len(kargs)==0:
			instance = klass()
		elif len(args)==0:
			instance = apply(klass,kargs)
		elif len(kargs)==0:
			instance = apply(klass,args)
		else: instance = apply(klass,args,kargs)

		return instance

	def createCan(self, canName, *args, **kwargs):
		##Looks in the directories specified in the application.canDirs List
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
		else: instance = apply(klass,args,kwargs)
		return instance
	

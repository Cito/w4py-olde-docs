
import os

class CanFactory:
    """Creates Cans on demand.  Looks only in the Cans directory of WebKit."""
    def __init__(self, app,canDir):
	    self.__CanClasses={}
	    self.__App = app
	    #self.__CanDir = app.getCanDir()
	    self.__CanDir=canDir

    def createCan(self,canName,*args,**kargs):

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
	
	
	

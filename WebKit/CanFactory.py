
import os
import imp
import sys
import string

class CanFactory:
	"""
	Creates Cans on demand.
	Call createCan with a full package name, and any args to be passed to the Can's constructor.

	This Factory is used by the utility methods in Page and Servlet.

	The factory is placed in Application._canFactory.
	"""
	def __init__(self, app):
		self._canClasses={}
		self._app = app



	def createCan(self, canName, *args, **kwargs):

		debug = 0
		if debug: from pprint import pprint
		klass = self._canClasses.get(canName, None)
		if not klass:
			
			if debug: print "Creating can for ", canName
			className = string.split(canName,".")[-1]
			mod = __import__(canName,locals(), globals(), [canName])
			if debug:
				pprint( mod )
		
			klass = mod.__dict__[className]
				
		self._canClasses[canName]=klass

		if debug:
			print klass
			print type(klass)

		if len(args)==0 and len(kwargs)==0:
			instance = klass()
		elif len(args)==0:
			instance = apply(klass,kwargs)
		elif len(kwargs)==0:
			instance = apply(klass,args)
		else:
			instance = apply(klass,args,kwargs)

		if debug:
			pprint( instance )
			pprint (dir(instance))
		return instance


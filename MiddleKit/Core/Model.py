import os
from types import ClassType


class Model:
	'''
	A Model defines the classes, attributes and enumerations of an application.

	It also provides access to the Python classes that implement these structures for use by other MiddleKit entities including code generators and object stores.
	'''

	def __init__(self, filename=None, customCoreClasses= {}):
		self._filename = None
		self._coreClasses = customCoreClasses
		self._klasses = None
		if filename!=None:
			self.read(filename)

	def name(self):
		if self._name is None:
			if self._filename:
				self._name = os.path.splitext(os.path.basename(self._filename))[0]
			else:
				self._name = 'unnamed-mk-model'
		return self._name

	def read(self, filename):
		assert self._filename is None, 'Cannot read twice.'
		# Assume the .mkmodel extension if none is given
		if os.path.splitext(filename)[1]=='':
			filename += '.mkmodel'
		self._filename = filename
		self._name = None
		self.klasses().read(os.path.join(filename, 'Classes.csv'))

	def coreClass(self, className):
		''' For the given name, returns a class from MiddleKit.Core or the custom set of classes that were passed in via initialization. '''
		pyClass = self._coreClasses.get(className, None)
		if pyClass is None:
			results = {}
			exec 'import MiddleKit.Core.%s as module'%className in results
			pyClass = getattr(results['module'], className)
			assert type(pyClass) is ClassType
			self._coreClasses[className] = pyClass
		return pyClass

	def coreClassNames(self):
		''' Returns a list of model class names found in MiddleKit.Core. '''
		# a little cheesy, but it does the job:
		import MiddleKit.Core as Core
		return Core.__all__

	def klasses(self):
		''' Return an instance that inherits from Klasses, using the base classes passed to __init__, if any. '''
		if self._klasses is None:
			Klasses = self.coreClass('Klasses')
			self._klasses = Klasses(self)
		return self._klasses

	def klass(self, name):
		return self._klasses[name]

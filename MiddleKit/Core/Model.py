import os
from types import ClassType
from MiscUtils.Configurable import Configurable
from MiscUtils import NoDefault


class Model(Configurable):
	'''
	A Model defines the classes, attributes and enumerations of an application.

	It also provides access to the Python classes that implement these structures for use by other MiddleKit entities including code generators and object stores.
	'''

	def __init__(self, filename=None, customCoreClasses={}, rootModel=None):
		Configurable.__init__(self)
		self._filename = None
		self._coreClasses = customCoreClasses
		self._klasses = None
		self._parents = []  # e.g., parent models

		# _allModelsByFilename is used to avoid loading the same parent model twice
		if rootModel:
			self._allModelsByFilename = rootModel._allModelsByFilename
		else:
			self._allModelsByFilename = {}
		self._rootModel = rootModel

		if filename!=None:
			self.read(filename)

	def name(self):
		if self._name is None:
			if self._filename:
				self._name = os.path.splitext(os.path.basename(self._filename))[0]
			else:
				self._name = 'unnamed-mk-model'
		return self._name

	def setName(self, name):
		self._name = name

	def filename(self):
		return self._filename

	def read(self, filename):
		assert self._filename is None, 'Cannot read twice.'
		# Assume the .mkmodel extension if none is given
		if os.path.splitext(filename)[1]=='':
			filename += '.mkmodel'
		self._filename = os.path.abspath(filename)
		self._name = None
		self.readParents()
		self.klasses().read(os.path.join(filename, 'Classes.csv'))

		# create containers for all klasses, uniqued by name
		models = list(self._searchOrder)
		models.reverse()
		byName = {}
		inOrder = []
		for model in models:
			for klass in model.klasses().klassesInOrder():
				name = klass.name()
				if byName.has_key(name):
					for i in range(len(inOrder)):
						if inOrder[i].name()==name:
							inOrder[i] = klass
				else:
					inOrder.append(klass)
				byName[name] = klass
		assert len(byName)==len(inOrder)
		for name, klass in byName.items():
			assert klass is self.klass(name)
		for klass in inOrder:
			assert klass is self.klass(klass.name())
		self._allKlassesByName = byName
		self._allKlassesInOrder = inOrder

	def readParents(self):
		"""
		Reads the parent models of the current model, as
		specified in the 'Inherit' setting.

		The attributes _parents and _searchOrder are set.
		"""
		for filename in self.setting('Inherit', []):
			filename = os.path.abspath(os.path.join(os.path.dirname(self._filename), filename))
			if self._allModelsByFilename.has_key(filename):
				model = self._allModelsByFilename[filename]
				assert model!=self._rootModel
			else:
				model = self.__class__(filename, self._coreClasses, self)
				self._allModelsByFilename[filename] = model
			self._parents.append(model)

		# establish the search order
		# algorithm taken from http://www.python.org/2.2/descrintro.html#mro
		searchOrder = self.allModelsDepthFirstLeftRight()

		# remove duplicates:
		indexes = range(len(searchOrder))
		indexes.reverse()
		for i in indexes:
			model = searchOrder[i]
			j = 0
			while j<i:
				if searchOrder[j] is model:
					del searchOrder[j]
					i -= 1
				else:
					j += 1

		self._searchOrder = searchOrder


	def allModelsDepthFirstLeftRight(self, parents=None):
		"""
		Returns a list of all models, including self, parents and
		ancestors, in a depth-first, left-to-right order. Does not
		remove duplicates (found in inheritance diamonds).

		Mostly useful for readParents() to establish the lookup
		order regarding model inheritance.
		"""
		if parents is None:
			parents = []
		parents.append(self)
		for parent in self._parents:
			parent.allModelsDepthFirstLeftRight(parents)
		return parents

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
		"""
		Return an instance that inherits from Klasses, using the base
		classes passed to __init__, if any.

		See also: klass(), allKlassesInOrder(), allKlassesByName()
		"""
		if self._klasses is None:
			Klasses = self.coreClass('Klasses')
			self._klasses = Klasses(self)
		return self._klasses

	def klass(self, name, default=NoDefault):
		"""
		Returns the klass with the given name, searching the parent
		models if necessary.
		"""
		for model in self._searchOrder:
			klass = model.klasses().get(name, None)
			if klass:
				return klass
		if default is NoDefault:
			raise KeyError, name
		else:
			return default

	def allKlassesInOrder(self):
		"""
		Returns a sequence of all the klasses in this model, unique by
		name, including klasses inherited from parent models.

		The order is the order of declaration, top-down.
		"""
		return self._allKlassesInOrder

	def allKlassesByName(self):
		"""
		Returns a dictionary of all the klasses in this model, unique
		by name, including klasses inherited from parent models.
		"""
		return self._allKlassesByName


	## Being configurable ##

	def configFilename(self):
		if self._filename is None:
			return None
		else:
			return os.path.join(self._filename, 'Settings.config')

	def defaultConfig(self):
		return {
			'Threaded': 1,
		}

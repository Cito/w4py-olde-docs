from UserDict import UserDict
from ModelObject import ModelObject
from MiscUtils import NoDefault
import types


class Klass(UserDict, ModelObject):
	'''
	A Klass represents a class specification consisting primarily of a name and a list of attributes.
	'''

	## Init ##

	def __init__(self, dict=None):
		''' Initializes a Klass definition with a raw dictionary, typically read from a file. The 'Class' field contains the name and can also contain the name of the superclass (like "Name : SuperName"). Multiple inheritance is not yet supported. '''
		UserDict.__init__(self, {})
		self._attrsList = []
		self._attrsByName = {}
		self._superklass = None
		self._subklasses = []
		if dict is not None:
			self.readDict(dict)


	## Reading ##

	def readDict(self, dict):
		name = dict['Class']
		if '(' in name:
			assert ')' in name, 'Invalid class spec. Missing ).'
			self._name, rest = name.split('(')
			self._supername, rest = rest.split(')')
			assert rest.strip()==''
			self._name = self._name.strip()
			self._supername = self._supername.strip()
		elif ':' in name:
			# deprecated: we used to use a C++-like syntax involving colons
			# instead of a Python-like syntax with parens
			parts = [part.strip() for part in name.split(':')]
			if len(parts)!=2:
				raise RuntimeError, 'Invalid class spec: %s' % string
			self._name, self._supername = parts
		else:
			self._name = name
			self._supername = dict.get('Super', 'MiddleObject')
		self._isAbstract = dict.get('isAbstract', 0)

		# fill in UserDict with the contents of this dict
		for key, value in dict.items():
			# @@ 2001-02-21 ce: should we always strip string fields? Probably.
			if type(value) is types.StringType and value.strip()=='':
				value = None
			self[key] = value


	def awakeFromRead(self):
		''' Performs further initialization. Invoked by Klasses after all basic Klass definitions have been read. '''
		self._makeAllAttrs()

	def _makeAllAttrs(self):
		''' Makes the all attributes list which is accessible via allAttrs(). Invoked by awakeFromRead(). '''
		klass = self
		klasses = []
		while 1:
			klasses.append(klass)
			klass = klass.superklass()
			if klass is None:
				break
		klasses.reverse()

		attrs = []
		for klass in klasses:
			attrs.extend(klass.attrs())

		self._allAttrs = attrs


	## Names ##

	def name(self):
		return self._name

	def supername(self):
		return self._supername


	## Id ##

	def id(self):
		''' Returns the id of the class, which is an integer. Ids can be fundamental to storing object references in concrete object stores. This method will throw an exception if setId() was not previously invoked. '''
		return self._id

	def setId(self, id):
		self._id = id


	## Superklass ##

	def superklass(self):
		return self._superklass

	def setSuperklass(self, klass):
		assert self._superklass is None, "Can't set superklass twice."
		self._superklass = klass
		klass.addSubklass(self)


	## Ancestors ##

	def lookupAncestorKlass(self, name, default=NoDefault):
		"""
		Searches for and returns the ancestor klass with the given
		name. Raises an exception if no such klass exists, unless a
		default is specified (in which case it is returned).
		"""
		if self._superklass:
			if self._superklass.name()==name:
				return self._superklass
			else:
				return self._superklass.lookupAncestorKlass(name, default)
		else:
			if default is NoDefault:
				raise KeyError, name
			else:
				return default

	def isKindOfKlassNamed(self, name):
		"""
		Returns true if the klass is the same as, or inherits from,
		the klass with the given name.
		"""
		if self.name()==name:
			return 1
		else:
			return self.lookupAncestorKlass(name, None) is not None


	## Subklasses ##

	def subklasses(self):
		return self._subklasses

	def addSubklass(self, klass):
		self._subklasses.append(klass)


	## Accessing attributes ##

	def addAttr(self, attr):
		self._attrsList.append(attr)
		self._attrsByName[attr.name()] = attr
		attr.setKlass(self)

	def attrs(self):
		''' Returns a list of all the klass' attributes. '''
		return self._attrsList

	def hasAttr(self, name):
		return self._attrsByName.has_key(name)

	def attr(self, name, default=NoDefault):
		''' Returns the attribute with the given name. If no such attribute exists, an exception is raised unless a default was provided (which is then returned). '''
		if default is NoDefault:
			return self._attrsByName[name]
		else:
			return self._attrsByName.get(name, default)

	def lookupAttr(self, name, default=NoDefault):
		if self._attrsByName.has_key(name):
			return self._attrsByName[name]
		if self._superklass:
			return self._superklass.lookupAttr(name, default)
		else:
			if default is NoDefault:
				raise KeyError, name
			else:
				return default

	def allAttrs(self, isDerived=None):
		'''
		Returns a list of all attributes, including those inherited. The order is top down; that is, ancestor attributes come first.
		If isDerived=0, return only non-derived attrs; if isDerived=1, return only derived attrs.
		If this method fails, because of an unknown attribute, then awakeFromRead() has not yet been invoked.
		'''
		if isDerived is None:
			return self._allAttrs
		elif not isDerived:
			return [attr for attr in self._allAttrs if not attr.get('isDerived', 0)]
		else:
			return [attr for attr in self._allAttrs if attr.get('isDerived', 0)]

	## Klasses access ##

	def klasses(self):
		return self._klasses

	def setKlasses(self, klasses):
		''' Sets the klasses object of the klass. This is the klass' owner. '''
		self._klasses = klasses


	## Other access ##

	def isAbstract(self):
		return self._isAbstract


	## As string ##

	def asShortString(self):
		return '<Klass, %s, %x, %d attrs>' % (self._name, id(self), len(self._attrsList))

	def __str__(self):
		return self.asShortString()

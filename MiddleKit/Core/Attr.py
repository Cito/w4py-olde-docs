from ModelObject import ModelObject
from UserDict import UserDict
from MiscUtils import NoDefault
import re
from MiddleKit import StringTypes

nameRE = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*)$')


class Attr(UserDict, ModelObject):
	"""
	An Attr represents an attribute of a Klass mostly be being a dictionary-like object.
	"""

	def __init__(self, dict):
		UserDict.__init__(self, {})
		for key, value in dict.items():
			if key=='Attribute':
				key = 'Name'
			# @@ 2001-02-21 ce: should we always strip string fields? Probably.
			if isinstance(value, StringTypes) and value.strip()=='':
				value = None
			self[key] = value
		match = nameRE.match(self['Name'])
		if match is None or len(match.groups())!=1:
			raise ValueError, 'Bad name (%r) for attribute: %r.' % (self['Name'], dict)

	def name(self):
		return self.data['Name']

	def boolForKey(self, key):
		"""
		Returns True or False for the given key. Returns False if the
		key does not even exist. Raises a value error if the key
		exists, but cannot be parsed as a bool.
		"""
		original = self.get(key, '')
		s = original
		if isinstance(s, StringTypes):
			s = s.lower().strip()
		if s in (False, '', None, 0, 0.0, '0', 'false'):
			return False
		elif s in (True, 1, '1', 1.0, 'true'):
			return True
		else:
			raise ValueError, '%r for attr %r should be a boolean value (1, 0, True, False) but is %r instead' % (
				key, self.get('Name', '(UNNAMED)'), original)

	def isRequired(self):
		"""
		Returns true if a value is required for this attribute. In Python, that means the
		value cannot be None. In relational theory terms, that means the value cannot be
		NULL.
		"""
		return self.boolForKey('isRequired')

	def setKlass(self, klass):
		""" Sets the klass that the attribute belongs to. """
		self._klass = klass

	def klass(self):
		"""
		Returns the klass that this attribute is declared in and, therefore, belongs to.
		"""
		return self._klass

	def pyGetName(self):
		""" Returns the name that should be used for the Python "get" accessor method for this attribute. This implementation returns the name as it is, so the get methods are obj.foo(). """
		return self.name()

	def pySetName(self):
		""" Returns the name that should be used for the Python "set" accessor method for this attribute. This implementation returns setName, as in obj.setFoo(). """
		name = self.name()
		return 'set'+name[0].upper()+name[1:]

	def setting(self, name, default=NoDefault):
		"""
		Returns the value of a particular configuration setting taken
		from the model.

		Implementation note: Perhaps a future version should ask the
		klass and so on up the chain.
		"""
		return self.model().setting(name, default)

	def model(self):
		return self._klass.klasses()._model

	def awakeFromRead(self):
		pass


	## Warnings ##

	def printWarnings(self, out):
		pass

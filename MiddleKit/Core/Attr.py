from ModelObject import ModelObject
from UserDict import UserDict


class Attr(UserDict, ModelObject):
	'''
	An Attr represents an attribute of a Klass mostly be being a dictionary-like object.
	'''

	def __init__(self, dict):
		UserDict.__init__(self, {})
		for key, value in dict.items():
			if key=='Attribute':
				key = 'Name'
			self[key] = value

	def name(self):
		return self['Name']

	def isRequired(self):
		''' Returns true if a value is required for this attribute. In Python, that means the value cannot be None. In relational theory terms, that means the value cannot be NULL. '''
		if not self.has_key('isRequired'):
			req = 1
		else:
			req = self['isRequired']
			if req=='':
				req = '1'
		return int(req)
		# @@ 2000-11-11 ce: we say int() above, but in the future we
		# should provide specific types for the columns of the model

	def setKlass(self, klass):
		''' Sets the klass that the attribute belongs to. '''
		self._klass = klass

	def klass(self):
		return self._klass

	def pyGetName(self):
		''' Returns the name that should be used for the Python "get" accessor method for this attribute. This implementation returns the name as it is, so the get methods are obj.foo(). '''
		return self.name()

	def pySetName(self):
		''' Returns the name that should be used for the Python "set" accessor method for this attribute. This implementation returns setName, as in obj.setFoo(). '''
		name = self.name()
		return 'set'+name[0].upper()+name[1:]

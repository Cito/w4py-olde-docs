from types import *
import string, sys
from time import time


# if technique is zero, use bound methods in the _kvGetBindings cache, otherwise use unbound
# @@ 2000-05-31 ce: after additional testing we can probably scorge the technique=0 allowance
technique = 1

class NamedValueAccess:
	'''	This class is intended to be ancestor class such that you can say:
			from NamedValueAccess import *
			age = someObj.valueForName("age")
			name = someObj.valueForName("info.fields.name")

		This can be useful in setups where you wish to textually refer to the objects
		in a program, such as an HTML template processed in the context of an
		object-oriented framework.

		Keys can be matched to either methods or ivars and with or without underscores.

		valueForName() can also traverse bona fide dictionaries (DictType).

		You can safely import * from this module. Only the NamedValueAccess class is exported
		(other than typical things like string and sys).

		There is no __init__() method and never will be.

		You can run the test suite by running this module as a program.

		You'll see the terms 'key' and 'name' in the class and its documentation. A 'key'
		is a single identifier such as 'foo'. A name could be key, or a qualified key,
		such as 'foo.bar.boo'. Names are generally more convenient and powerful, while
		key-oriented methods are more efficient and provide the atomic functionality that
		name-oriented methods are built upon. From a usage point of view, you normally
		just use the 'name' methods and forget about the 'key'.

		@@ 2000-05-21 ce: This class causes problems when used in WebKit for logging.
			Perhaps circular references?
			Involving self?
			Having to do with methods bound to their objects?

		@@ 2000-03-03 ce: document ivars

		@@ 2000-04-24 ce: Some classes like UserDict need to use getitem()
		instead of getattr() and don't need to deal with _bindingForGetKey().

		@@ 2000-05-31 ce: Rename this class to NamedValues, NamedValueAccess, ValuesByName

		@@ This class probably needs to be in MiscUtils, as it's being used in that way
		   while MiddleKit was intended for "enterprise/business objects".
	'''

	#
	# Accessing values by key
	#
	def hasValueForKey(self, key):
		'''	Returns true if the key is available, although that does not
			guarantee that there will not be errors caused by retrieving the key. '''

		return self._bindingForGetKey(key)!=None


	def valueForKey(self, key, default=None):
		''' Suppose key is 'foo'. This method returns the value with the following precedence:
				1. Methods before non-methods
				2. Public attributes before private attributes

			More specifically, this method then returns one of the following:
				* self.foo()
				* self._foo()
				* self.foo
				* self._foo

			...or default, if it is not None,
			otherwise invokes and returns result of handleUnknownGetKey().

			See valueForName() which is a more advanced version of this method that allows
			multiple, qualified keys.
		'''

		binding = self._bindingForGetKey(key)

		if not binding:
			if default is None:
				return self.handleUnknownGetKey(key)
			else:
				return default

		if type(binding) is MethodType:
# @@ 2000-05-07 ce: come to a decision on exception handling for key errors
#			try:
			if technique:
				result = binding(self)
			else:
				result = binding()
#			except:
				# @@ 2000-02-18: Improve next line with exception info
#				raise 'NamedValueAccess', 'Caught exception while accessing key (%s). Exception is %s' % (key, sys.exc_info())
			return result
		else:
			return getattr(self, binding)

	def hasValueForName(self, keysString):
		try:
			value = self.valueForName(keysString)
		except 'NamedValueAccess':
			return 0
		return 1

	def valueForName(self, keysString, default=None):
		''' Returns the value for the given keysString. This is the more advanced version of
			valueForKey(), which can only handle single names. This method can handle
			'foo', 'foo1.foo2', 'a.b.c.d', etc. It will traverse dictionaries if needed. '''
		keys = string.split(keysString, '.')
		return self.valueForKeySequence(keys, default)

	def valueForKeySequence(self, listOfKeys, default=None):
		# @@ 2000-02-18: document
		return _valueForKeySequence(self, listOfKeys, default)

	def valuesForNames(self, keys, default=None, defaults=None, forgive=0, includeNames=0):
		''' Returns a list of values that match the given keys, each of which is passed
			  through valueForName() and so could be of the form 'a.b.c'.
			keys is a sequence. default is any kind of object. defaults is a sequence.
			  forgive and includeNames is a flag.
			If default is not None, then it is substituted when a key is not found.
			Otherwise, if defaults is not None, then it's corresponding/parallel value
			  for the current key is substituted when a key is not found.
			Otherwise, if forgive=1, then unknown keys simply don't produce any values.
			Otherwise, if default and defaults are None, and forgive=0, then the unknown
			  keys will probably raise an exception through self.handleUnknownGetKey() although
			  that method can always return a final, default value.
			if keys is None, then None is returned. If keys is an empty list, then None
			  is returned.
			Often these last four arguments are specified by key.
			Examples:
				names = ['origin.x', 'origin.y', 'size.width', 'size.height']
				obj.valuesForNames(names)
				obj.valuesForNames(names, default=0.0)
				obj.valuesForNames(names, defaults=[0.0, 0.0, 100.0, 100.0])
				obj.valuesForNames(names, forgive=0)
			@@ 2000-03-04 ce: includeNames is only supported when forgive=1.
				It should be supported for the other cases.
				It should be documented.
				It should be included in the test cases.
		'''

		if keys is None:
			return None
		if len(keys) is 0:
			return []
		results = []

		if default is not None:
			results = map(lambda key, myself=self, mydefault=default: myself.valueForName(key, mydefault), keys)
		elif defaults is not None:
			if len(keys) is not len(defaults):
				raise 'NamedValueAccess', 'Keys and defaults have mismatching lengths (%d and %d).' % (len(keys), len(defaults))
			results = map(lambda key, default, myself=self: myself.valueForName(key, default), keys, defaults)
		elif forgive:
			results = []
			uniqueObject = 'uni' + 'que'
			for key in keys:
				value = self.valueForName(key, uniqueObject)
				if value is not uniqueObject:
					if includeNames:
						results.append((key, value))
					else:
						results.append(value)
		else:
			# no defaults, no forgiveness
			results = map(lambda key, myself=self: myself.valueForName(key), keys)
		return results

	def setValueForKey(self, key, value):
		# @@ 2000-02-18: naming might be weired here with args reversed
		''' Suppose key is 'foo'. This method sets the value with the following precedence:
				1. Public attributes before private attributes
				2. Methods before non-methods

			More specifically, this method then uses one of the following:
				@@ 2000-03-04 ce: fill in

			...or invokes handleUnknownSetKey().
		'''
		raise 'KeyValue', 'Not implemented' # @@ 2000-03-04 ce

	def resetKeyBindings(self):
		# @@ 2000-02-18 document this method
		if hasattr(self, '_kvGetBindings'):
			self._kvGetBindings = {}


	#
	# Errors
	#
	def handleUnknownGetKey(self, key):
		raise 'NamedValueAccess', key

	def handleUnknownSetKey(self, key):
		raise 'NamedValueAccess', key


	#
	# Private
	#
	def _bindingForGetKey(self, key):
		'''	Bindings are cached.
			Bindings are methods or strings.
		'''

		# Make _kvGetBindings dictionary if we don't have one
		if not hasattr(self, '_kvGetBindings'):
			self._kvGetBindings = {}

		# Return the binding if we already have one
		if self._kvGetBindings.has_key(key):
			return self._kvGetBindings[key]

		# No binding, so we have to look for the key

		found = None  # set to what we find

		# Try plain old key
		if hasattr(self, key):
			found = getattr(self, key)
			#print '0: found = ', found, type(found)
			if type(found) is not MethodType:
				found = key
			elif technique:
				found = getattr(self.__class__, key)
			self._kvGetBindings[key] = found
		#print '1: found = ', found, type(found)

		# Try _key only if we didn't find a method called key
		if type(found) is not MethodType:
			underKey = '_' + key
			if hasattr(self, underKey):
				underAttr = getattr(self, underKey)
				if found==None:
					if type(underAttr) is MethodType:
						if technique:
							value = getattr(self.__class__, underKey)
						else:
							value = underAttr
					else:
						value = underKey
					found = self._kvGetBindings[key] = value
				else:
					if type(underAttr) is MethodType:
						if technique:
							underAttr = getattr(self.__class__, underKey)
						found = self._kvGetBindings[key] = underAttr

		#print '2: found = ', found, type(found)

		return found


#
# Private
#

def _valueForKeySequence(obj, listOfKeys, default=None):
	'''	This is a recursive function used to implement NamedValueAccess.valueForKeySequence.
		Besides supporting inheritors of NamedValueAccess, this function also supports
		dictionaries, which is why it's not found in the class.
	'''

	# @@ 2000-02-18: Optimize by specifying index instead of making new list
	if type(obj) is DictType:
		try:
			value = obj[listOfKeys[0]]
		except: # @@ 2000-03-03 ce: this exception should be more specific. probably nameerror or indexerror
			if default is None:
				raise 'NamedValueAccess', 'Unknown key (%s) in dictionary.' % listOfKeys[0]
			else:
				return default
	else:
		value = obj.valueForKey(listOfKeys[0], default)
	if len(listOfKeys)>1:
		return _valueForKeySequence(value, listOfKeys[1:], default)
	else:
		return value


#
# Testing
#
class _t1(NamedValueAccess):
	def foo(self):
		return 1

class _t2(NamedValueAccess):
	def _foo(self):
		return 1

class _t3(NamedValueAccess):
	def foo(self):
		return 1
	def _foo(self):
		return 0

class _t4(NamedValueAccess):
	def foo(self):
		return 1
	def __init__(self):
		self._foo = 0

class _t5(NamedValueAccess):
	def __init__(self):
		self.foo = 0
	def _foo(self):
		return 1

class _t6(NamedValueAccess):
	def __init__(self):
		self.foo = 1
		self._foo = 0

class _t7(NamedValueAccess):
	def handleUnknownGetKey(self, key):
		return 1

def _testHeader(header):
	header = 'TESTING: ' + header
	print
	print header
	print '-' * len(header)

def _testUse():
	# @@ 2000-03-03 ce: Instead of having to scan the output, these tests should all raise exceptions if they fail (e.g., use assert)
	# @@ 2000-03-03 ce: Still need to test that exceptions are thrown as appropriate
	print 'Begin Testing', __name__

	_testHeader('Basic access')
	print 'All foos below should be 1, not 0.'
	classes = [_t1, _t2, _t3, _t4, _t5, _t6, _t7]
	for theClass in classes:
		print '<<%s>>' % theClass.__name__
		print theClass().valueForKey('foo')
		print

	_testHeader('Repeated access')
	print 'Should print all 1s.'
	objects = map(lambda theClass: theClass(), classes)
	for x in range(8): # 8 - just for repetition
		for obj in objects:
			print obj
			assert obj.valueForKey('foo')==1
	print '\n'

	_testHeader('Compound keys')
	print 'Should print all 1s.'
	# link the objects
	for i in range(len(objects)-1):
		objects[i].nextObject = objects[i+1]
	# test the links
	for i in range(len(objects)):
		compoundKey = 'nextObject.' * i + 'foo'
		print '%d. compound key == '%i, compoundKey
		print 'value == ', objects[0].valueForName(compoundKey)
		print

	_testHeader('Compound keys with dictionaries')
	obj = objects[0]
	obj.rect = { 'origin': {'x':1, 'y':2},  'size': {'width':3, 'height':4} }
	print 'obj.rect.origin.x == 1 ==', obj.valueForName('rect.origin.x')


	_testHeader('Default values')
	obj = _t1()
	key = 'notThere'
	assert obj.valueForKey(key, 1)==1
	assert obj.valueForName(key, 1)==1
	obj.dict = {'foo': 'foo'}
	assert obj.valueForName('dict.notThere', 1)==1
	obj.dict['obj'] = _t1()
	assert obj.valueForName('dict.obj.notThere', 1)==1


	_testHeader('valuesForNames(self, keys, default=None, defaults=None, forgive=0)')

	# set up structure: rect(attrs(origin(x, y), size(width, height)))
	rect = _t1()
	origin = _t1();  origin.x = 5;  origin.y = 6
	size = _t1();  size.width = 43;  size.height = 87;
	attrs = {'origin': origin, 'size': size}
	rect.attrs = attrs

	# test integrity of structure and validity of valueForName()
	assert rect.valueForName('attrs') is attrs
	assert rect.valueForName('attrs.origin') is origin
	assert rect.valueForName('attrs.size') is size

	# test valuesForNames()
	notFound = 'notFound'
	assert rect.valuesForNames(['attrs', 'attrs.origin', 'attrs.size']) == [attrs, origin, size]
	assert rect.valuesForNames(['attrs.dontFind', 'attrs', 'attrs.origin.dontFind'], default=notFound) == [notFound, attrs, notFound]
	assert rect.valuesForNames(['attrs.dontFind', 'attrs', 'attrs.origin.dontFind'], defaults=[1, 2, 3]) == [1, attrs, 3]
	assert rect.valuesForNames(['attrs.dontFind', 'attrs', 'attrs.origin.dontFind'], forgive=1) == [attrs]

	print 'End Testing', __name__


def _testLeaks():
	# As of 2000-05-30 we have a leak: The cached key-value bindings using bound method objects which refer to self, thereby creating a cyclic reference.
	if len(sys.argv)>2:
		count = int(sys.argv[2])
	else:
		usage()
	start = time()
	for i in xrange(count):
		t = _t1()
		t.valueForKey('foo')
		#print t._kvGetBindings
	print '%0.2f secs' % (time()-start)


def usage():
	sys.stdout = sys.stderr
	print "NamedValueAccess.py can be used as a program to invoke it's test suite."
	print 'usage:'
	print '  NamedValueAccess.py use'
	print '  NamedValueAccess.py leaks <iterations>'
	print
	sys.exit(1)


if __name__=='__main__':
	if len(sys.argv)<2:
		usage()
	elif sys.argv[1]=='use':
		_testUse()
	elif sys.argv[1]=='leaks':
		_testLeaks()
	else:
		usage()

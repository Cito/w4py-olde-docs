from MiscUtils.NamedValueAccess import NamedValueAccess
from MiscUtils import NoDefault
import ObjectStore
import sys, types
from MiddleKit.Core.ObjRefAttr import ObjRefAttr
from types import StringType


class MiddleObject(NamedValueAccess):
	"""
	MiddleObject is the abstract superclass of objects that are
	manipulated at runtime by MiddleKit. For any objects that you
	expect to pull out of a database via MiddleKit, their classes must
	inherit MiddleObject.

	MiddleObjects have a serial number which persists in the database
	and is unique for the object across all timelines. In other words,
	serial numbers do not get reused.

	A serial number of 0 is not valid for persistence, so if a
	MiddleObject has such a serial number, you will know that it was
	not created from the database and it has not yet been committed to
	the database (upon which time it will receive a valid serial
	number).

	Normally we simply prefix data attributes with '_', but here we
	prefix them with '_mk_'. Part of the reason is to provide an extra
	degree of protection for subclasses from current and future
	attribute names used for MiddleKit's own internal book keeping
	purposes. Although users of MiddleKit subclass MiddleObject, they
	only need to have a limited understanding of it. Also, in
	__setattr__ we skip the change-detection bookkeeping on	'_mk_*'
	attributes.
	"""


	## Init ##

	def __init__(self, store=None): # @@ 2000-09-21 ce: do we really need the store here?
		self.__dict__['_mk_initing'] = 1
		if store is None:
			self._mk_store = ObjectStore.Store
		else:
			self._mk_store = store
		self._mk_klass           = None  # Our class model
		self._mk_changedAttrs    = None
		self._mk_serialNum       = 0
		self._mk_key             = None
		self._mk_changed         = 0
		self._mk_initing         = 0
		self._mk_inStore         = 0
		self._mk_backObjRefAttrs = None

	_mk_setCache = {}    # cache the various setFoo methods first by qualified class name

	def initFromRow(self, row):
		fullClassName = self.__class__.__module__ + '.' + self.__class__.__name__
		cache = self._mk_setCache.setdefault(fullClassName, [])
		if not cache:
			allAttrs = self.klass().allDataAttrs()
			# @@ 2000-10-29 ce: next line is major hack: hasSQLColumn()
			attrs = [attr for attr in allAttrs if attr.hasSQLColumn()]
			attrNames = [attr.name() for attr in attrs]
			assert len(attrNames)+1==len(row)  # +1 because row has serialNumber
			for name in attrNames:
				setMethodName = 'set' + name[0].upper() + name[1:]
				setMethod = getattr(self.__class__, setMethodName, '_'+name)
				cache.append(setMethod)

		assert len(cache)+1==len(row)
		dict = self.__dict__ # we use this to bypass our own __setattr__
		dict['_mk_initing'] = 1
		if self._mk_serialNum==0:
			self.setSerialNum(row[0])
		else:
			assert self._mk_serialNum==row[0]
		# Set all of our attributes with setFoo() or by assigning to _foo
		for i in xrange(len(cache)):
			value = row[i+1]
			setter = cache[i]
			if isinstance(setter, StringType):
				dict['_'+setter] = value
			else:
				# a method
				setter(self, value)
		dict['_mk_initing'] = 0
		dict['_mk_inStore'] = 1
		return self


	## Serial numbers ##

	def serialNum(self):
		return self._mk_serialNum

	def setSerialNum(self, value):
		''' Sets the serial number of the object and invalidates the object's key.
		There are some restrictions: Once the serial number is a positive value, indicating a legitimate value from the object store, it cannot be set to anything else. Also, if the serial number is negative, indicating a temporary serial number for new objects that haven't been committed to the database, it can only be set to a positive value.
		'''
		assert type(value) in (type(0), type(0L)), "Type is: %r, value is: %r" % (type(value), value)
		if self._mk_serialNum<0:
			assert value>0
		else:
			assert self._mk_serialNum==0
		self._mk_serialNum = value
		self._mk_key = None


	## Change ##

	def isChanged(self):
		return self._mk_changed

	def setChanged(self, flag):
		self._mk_changed = flag

	## In Store ##

	def isInStore(self):
		return self._mk_inStore

	def setInStore(self, flag):
		self._mk_inStore = flag


	## Keys ##

	def key(self):
		"""
		Returns the object's key as needed and used by the ObjectStore.
		Will return None if setKey() was never invoked, or not invoked
		after a setSerialNum().
		"""
		return self._mk_key

	def setKey(self, key):
		"""
		Restrictions: Cannot set the key twice.
		"""
		assert self._mk_serialNum>=1, "Cannot make keys for objects that haven't been persisted yet."
		assert self._mk_key is None
		self._mk_key = key


	## Misc utility ##

	def allAttrs(self, includeUnderscoresInKeys=1):
		"""
		Returns a dictionary mapping the names of attributes to their
		values. Only attributes defined in the MiddleKit object model
		are included. An example return value might be
			{ '_x': 1, '_y': 1 },
		or if includeUnderscoresInKeys==0,
			{ 'x': 1, 'y': 1 }.
		"""
		allAttrs = {}
		allAttrDefs = self.klass().allAttrs()
		for attrDef in allAttrDefs:
			if includeUnderscoresInKeys:
				key = attrName = '_'+attrDef.name()
			else:
				key = attrDef.name()
				attrName = '_' + key
			allAttrs[key] = getattr(self, attrName)
		return allAttrs

	def backObjRefAttrs(self):
		"""
		Returns a list of all ObjRefAttrs in the given object model that can
		potentially refer to this object.  The list does NOT include attributes
		inherited from superclasses.
		"""
		if self._mk_backObjRefAttrs is None:
			backObjRefAttrs = []
			# Construct targetKlasses = a list of this object's klass and all superklasses
			targetKlasses = []
			super = self.klass()
			while super:
				targetKlasses.append(super.name())
				super = super.superklass()
			# Look at all klasses in the model
			for klass in self.store().model().allKlassesInOrder():
				# find all ObjRefAttrs of this klass that refer to one of our targetKlasses
				for attr in klass.attrs():
					if isinstance(attr, ObjRefAttr) and attr.className() in targetKlasses:
						backObjRefAttrs.append(attr)
			self._mk_backObjRefAttrs = backObjRefAttrs
		return self._mk_backObjRefAttrs

	def referencingObjectsAndAttrs(self):
		"""
		Returns a list of tuples of (object, attr) for all objects that have
		ObjRefAttrs that reference this object.
		"""
		referencingObjectsAndAttrs = []
		selfSqlObjRef = self.sqlObjRef()
		for backObjRefAttr in self.backObjRefAttrs():
			objects = self.store().fetchObjectsOfClass(backObjRefAttr.klass(), **self.referencingObjectsAndAttrsFetchKeywordArgs(backObjRefAttr))
			for object in objects:
				assert object.valueForAttr(backObjRefAttr)==self
				referencingObjectsAndAttrs.append((object, backObjRefAttr))
		return referencingObjectsAndAttrs

	def referencingObjectsAndAttrsFetchKeywordArgs(self, backObjRefAttr):
		"""
		Used by referencingObjectsAndAttrs() to reduce the load on the persistent store.
		Specific object stores replace this as appropriate.
		"""
		return {}


	## Debugging ##

	def dumpAttrs(self, out=None, verbose=0):
		"""
		Prints the attributes of the object. If verbose is 0 (the
		default), then the only MiddleKit specific attribute that gets
		printed is _mk_serialNum.
		"""
		if out is None:
			out = sys.stdout
		out.write('%s %x\n' % (self.__class__.__name__, id(self)))
		keys = dir(self)
		keys.sort()
		keyWidth = max([len(key) for key in keys])
		for key in keys:
			if verbose:
				dump = 1
			else:
				dump = not key.startswith('_mk_') or key=='_mk_serialNum'
			if dump:
				name = key.ljust(keyWidth)
				out.write('%s = %s\n' % (name, getattr(self, key)))
		out.write('\n')


	## Misc access ##

	def store(self):
		return self._mk_store


	## Sneaky MiddleKit stuff ##

	def klass(self):
		if self._mk_klass is None:
			self._mk_klass = self._mk_store.model().klass(self.__class__.__name__)
		return self._mk_klass

	def addReferencedObjectsToStore(self, store):
		""" Adds all MK objects referenced by this object to the store """
		values = [self.valueForAttr(attr) for attr in self.klass().allDataAttrs()]
		for value in values:
			if isinstance(value, MiddleObject):
				store.addObject(value)
			elif isinstance(value, types.ListType):
				for obj in value:
					if isinstance(obj, MiddleObject):
						store.addObject(obj)


	## Accessing attributes by name ##

	def valueForKey(self, attrName, default=NoDefault):
		'''
		Returns the value of the named attribute by invoking its "get"
		accessor method. You can use this when you want a value whose
		name is determined at runtime.

		It also insulates you from the naming convention used for the
		accessor methods as defined in Attr.pyGetName(). For example,
		the test suites use this instead of directly invoking the "get"
		methods.

		If the attribute is not found, the default argument is returned
		if specified, otherwise LookupError is raised with the attrName.
		'''
		attr = self.klass().lookupAttr(attrName, None)
		if attr:
			return self.valueForAttr(attr, default)
		else:
			if default is NoDefault:
				raise LookupError, attrName
			else:
				return default

	def setValueForKey(self, attrName, value):
		'''
		Sets the value of the named attribute by invoking its "set"
		accessor method. You can use this when you want a value whose
		name is determined at runtime.

		It also insulates you from the naming convention used for the
		accessor methods as defined in Attr.pySetName(). For example,
		the test suites use this instead of directly invoking the "set"
		methods.

		If the required set method is not found, a LookupError is raised
		with the attrName.
		'''
		try:
			attr = self.klass().lookupAttr(attrName)
		except KeyError:
			method = None
		else:
			pySetName = attr.pySetName()
			method = getattr(self, pySetName, None)
		if method is None:
			raise LookupError, attrName
		return method(value)

	def valueForAttr(self, attr, default=NoDefault):
		getMethod = self.klass()._getMethods.get(attr.name(), None)
		if getMethod is None:
			pyGetName = attr.pyGetName()
			getMethod = getattr(self.klass().pyClass(), pyGetName, None)
			if getMethod is None:
				getMethod = 0  # 0 is false, and indicates that the search was already done
			self.klass()._getMethods[attr.name()] = getMethod
		if getMethod:
			try:
				return getMethod(self)
			except TypeError:
				assert 0, 'getMethod=%r, self=%r, type(self)=%r' % (getMethod, self, type(self))
		else:
			if default is NoDefault:
				raise LookupError, attr['Name']
			else:
				return default

	def setValueForAttr(self, attr, value):
		return self.setValueForKey(attr['Name'], value)

	# @@ 2001-07-10 ce: the old names
	#attr = valueForKey
	#setAttr = setValueForKey

	# @@ 2001-04-29 ce: This is for backwards compatibility only:
	# We can take out after the post 0.5.x version (e.g., 0.6 or 1.0)
	# or after 4 months, whichever comes later.
	_get = valueForKey
	_set = setValueForKey

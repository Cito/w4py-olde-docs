import sys
from types import ClassType, StringType
from MiscUtils import NoDefault
from ObjectKey import ObjectKey
from MiddleKit.Core.ModelUser import ModelUser
from MiddleKit.Core.Klass import Klass as BaseKlass
	# ^^^ for use in _klassForClass() below
	# Can't import as Klass or Core.ModelUser (our superclass)
	# will try to mix it in.


class ObjectStore(ModelUser):
	'''
	NOT IMPLEMENTED:
		* revertChanges()

	FUTURE
		* expanded fetch
	'''


	## Init ##

	def __init__(self):
		global Store
		if Store is None:
			Store = self
		self._model          = None
		self._hasChanges     = 0
		self._objects        = {} # keyed by ObjectKeys
		self._newObjects     = [] # @@ 2000-10-06 ce: should be a set?
		self._deletedObjects = []
		self._changedObjects = {} # a set
		self._newSerialNum   = -1


	## Manipulating the objects in the store ##

	def hasObject(self, object):
		raise NotImplementedError
		key = object.key()
		if key is None:
			return 0
		else:
			return self._objects.has_key(key)

	def object(self, key, default=NoDefault):
		''' Returns an object from the store by it's given key. If no default is given and the object is not in the store, then an exception is raised. Note: This method doesn't currently fetch objects from the persistent store. '''
		if default is NoDefault:
			return objects[key]
		else:
			return objects.get(key, default)

	def addObject(self, object):
		''' Restrictions: You cannot insert the same object twice. You cannot insert an object that was loaded from the store. '''
		#assert not self.hasObject(object)
		assert object.key()==None
		self.willChange()
		self._newObjects.append(object)
		# 2000-10-07 ce: Decided not to allow keys for non-persisted objects
		# Because the serial num, and therefore the key, will change
		# upon saving.
		#key = object.key()
		#if key is None:
		#	key = ObjectKey(object, self)
		#	object.setKey(key)
		#self._objects[key] = object

	def deleteObject(self, object):
		''' Restrictions: The object must be contained in the store and obviously you cannot remove it more than once. '''
		assert self.hasObject(object)
		self.willChange()
		self._deletedObjects.append(object)
		del self._objects[key]


	## Changes ##

	def hasChanges(self):
		return self._hasChanges

	def saveChanges(self):
		''' Commits object changes to the object store by invoking commitInserts(), commitUpdates() and commitDeletions() all of which must by implemented by a concrete subclass. '''
		self.commitInserts()
		self.commitUpdates()
		self.commitDeletions()
		self._hasChanges = 0

	def commitInserts(self):
		''' Invoked by saveChanges() to insert any news objects add since the last save. Subclass responsibility. '''
		raise SubclassResponsibilityError

	def commitUpdates(self):
		''' Invoked by saveChanges() to update the persistent store with any changes since the last save. '''
		raise SubclassResponsibilityError

	def commitDeletions(self):
		''' Invoked by saveChanges() to delete from the persistent store any objects deleted since the last save. Subclass responsibility. '''
		raise SubclassResponsibilityError

	def revertChanges(self):
		''' Discards all insertions and deletions, and restores changed objects to their original values. '''
		raise NotImplementedError

	def willChange(self):
		''' Invoked by self when the object store is changed. Sets a flag to record that fact. May be overridden by subclasses; super must be invoked. '''
		self._hasChanges = 1


	## Fetching ##

	def fetchObject(self, className, serialNum):
		raise SubclassResponsibilityError

	def fetchObjectsOfClass(self, className, isDeep=1):
		''' Fetches all objects of a given class. If isDeep is 1, then all subclasses are also returned. '''
		raise SubclassResponsibilityError


	## Other ##

	def clear(self):
		''' Clears all objects from the memory of the store. This does not delete the objects in the persistent backing. This method can only be invoked if there are no outstanding changes to be saved. You can check for that with hasChanges(). '''
		assert not self.hasChanges()
		assert len(self._newObjects)==0
		assert len(self._deletedObjects)==0
		assert len(self._changedObjects)==0

		self._objects        = {}
		self._newSerialNum   = -1


	## Notifications ##

	def objectChanged(self, object):
		'''
		MiddleObjects must send this message when one of their interesting attributes change, where an attribute is interesting if it's listed in the class model.
		This method records the object in a set for later processing when the store's changes are saved.
		If you subclass MiddleObject, then you're taken care of.
		'''
		self.willChange()
		self._changedObjects[object] = object  ## @@ 2000-10-06 ce: Should this be keyed by the object.key()? Does it matter?


	## Serial numbers ##

	def newSerialNum(self):
		''' Returns a new serial number for a newly created object. This is a utility methods for objects that have been created, but not yet committed to the persistent store. These serial numbers are actually temporary and replaced upon committal. Also, they are always negative to indicate that they are temporary, whereas serial numbers taken from the persistent store are positive. '''
		self._newSerialNum -= 1
		return self._newSerialNum


	## Self utility ##

	def _klassForClass(self, aClass):
		''' Returns a Klass object for the given class, which may be:
			- the Klass object already
			- a Python class
			- a class name (e.g., string)
		Users of this method include the various fetchObjectEtc() methods which take a "class" parameter.
		'''
		assert aClass is not None
		if not isinstance(aClass, BaseKlass):
			if type(aClass) is ClassType:
				aClass = self._model.klass(aClass.__name__)
			elif type(aClass) is StringType:
				aClass = self._model.klass(aClass)
			else:
				raise ValueError, 'Invalid class parameter. Pass a Klass, a name or a Python class. Type of aClass is %s. aClass is %s.' % (type(aClass), aClass)
		return aClass


# The singleton instance used by MiddleObject by default.
# This gets set by __init__ if it is None, so ordinarily
# you don't need to think about it.
Store = None


class Attr:

	def shouldRegisterChanges(self):
		''' MiddleObject asks attributes if changes should be registered. By default, all attributes respond true, but specific stores may choose to override this (a good example being ListAttr for SQLStore). '''
		return 1

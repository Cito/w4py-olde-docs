import sys, time
from types import InstanceType, LongType

from MiscUtils import NoDefault
from MiscUtils import Funcs as funcs

from MiddleObject import MiddleObject
from ObjectStore import ObjectStore, UnknownObjectError
from ObjectKey import ObjectKey
from MiscUtils.MixIn import MixIn
from MiddleKit.Core.ObjRefAttr import objRefJoin, objRefSplit


class SQLObjectStore(ObjectStore):
	'''
	TO DO:

		* _sqlEcho should be accessible via a config file setting as stdout, stderr or a filename.
	'''

	## Init ##

	def __init__(self, **kwargs):
		# @@ 2001-02-12 ce: We probably need a dictionary before kwargs for subclasses to pass to us in case they override __init__() and end up collecting kwargs themselves

		ObjectStore.__init__(self)
		self._dbArgs = kwargs
		self._connected = 0
		self._sqlEcho   = None
		self._sqlCount  = 0

		# @@ 2000-09-24 ce: resolve this
		import sys
		self._sqlEcho = sys.stdout

	def modelWasSet(self):
		''' Invokes self.connect(). '''
		ObjectStore.modelWasSet(self)
		self.connect()


	## Connecting to the db ##

	def isConnected(self):
		return self._connected

	def connect(self):
		''' Connects to the database only if the store has not already and provided that the story has a valid model.
		The default implementation of connect() is usually sufficient provided that subclasses have implemented createDBAPIConnection() and useDatabase(). '''
		assert self._model, 'Cannot connect: No model has been attached to this store yet.'
		if not self._connected:
			self._db = self.dbapiConnect()
			self._cursor = self._db.cursor()
			self._connected = 1
			self.useDB()
			self.readKlassIds()

	def dbapiConnect(self):
		'''
		Returns a DB API 2.0 connection. This is a utility method invoked by connect(). Subclasses should implement this, making use of self._dbArgs (a dictionary specifying host, username, etc.).
		Subclass responsibility.
		Example implementation:
			return MySQLdb.connect(**self._dbArgs)
		'''
		raise SubclassResponsibilityError

	def useDB(self):
		'''
		Takes whatever action necessary to use the appropriate database associated with the object store, usually named after self._model.name().
		This implementation performs a SQL "use MODELNAME;" so subclasses only need override if that doesn't work.
		'''
		self.executeSQL('use %s;' % self._model.name())

	def readKlassIds(self):
		''' Reads the klass ids from the SQL database. Should be invoked by connect(). '''
		self.executeSQL('select id, name from _MKClassIds;')
		klassesById = {}
		for (id, name) in self._cursor.fetchall():
			klass = self._model.klass(name)
			klassesById[id] = klass
			klass.setId(id)
		self._klassesById = klassesById


	## Changes ##

	def commitInserts(self):
		for object in self._newObjects:
			# New objects not in the persistent store have negative serial numbers
			assert object.serialNum()<1

			# SQL insert
			sql = object.sqlInsertStmt()
			self.executeSQL(sql)

			# Get new id/serial num
			idNum = self.retrieveLastInsertId()

			# Update object
			object.setSerialNum(idNum)
			object.setKey(ObjectKey().initFromObject(object))
			object.setChanged(0)

			# Update our object pool
			self._objects[object.key()] = object

		self._newObjects = []

	def retrieveLastInsertId(self):
		''' Returns the id (typically a 32-bit int) of the last INSERT operation by this connection. Used by commitInserts() to get the correct serial number for the last inserted object.
		Subclass responsibility. '''
		raise SubclassResponsibilityError

	def commitUpdates(self):
		for object in self._changedObjects.values():
			sql = object.sqlUpdateStmt()
			self.executeSQL(sql)
		self._changedObjects.clear()

	def commitDeletions(self):
		if len(self._deletedObjects):
			## @@ 2000-09-24 ce: implement this
			print '>> whoops! deletions not implemented'
			print


	## Fetching ##

	def fetchObject(self, aClass, serialNum, default=NoDefault):
		''' Fetches a single object of a specific class and serial number. TheClass can be a Klass object (from the MiddleKit object model), the name of the class (e.g., a string) or a Python class.
		Raises an exception if theClass parameter is invalid, or the object cannot be located.
		'''
		klass = self._klassForClass(aClass)
		where = 'where %s=%d' % (klass.sqlIdName(), serialNum)
		objects = self.fetchObjectsOfClass(klass, where)
		count = len(objects)
		if count==0:
			if default is NoDefault:
				raise UnknownObjectError, 'aClass = %r, serialNum = %r' % (aClass, serialNum)
			else:
				return default
		else:
			assert count==1
			return objects[0]

	def fetchObjectsOfClass(self, aClass, clauses='', isDeep=1):
		'''
		Fetches a list of objects of a specific class. The list may be empty if no objects are found.
		aClass can be a Klass object (from the MiddleKit object model), the name of the class (e.g., a string) or a Python class.
		The clauses argument can be any SQL clauses such as 'where x<5 order by x'. Obviously, these could be specific to your SQL database, thereby making your code non-portable. Use your best judgement.
		You should label all arguments other than aClass:
			objs = store.fetchObjectsOfClass('Foo', clauses='where x<5')
		The reason for labeling is that this method is likely to undergo improvements in the future which could include additional arguments. No guarantees are made about the order of the arguments except that aClass will always be the first.
		Raises an exception if aClass parameter is invalid.
		'''
		klass = self._klassForClass(aClass)
		objs = []
		if not klass.isAbstract():
			# @@ 2000-10-29 ce: Optimize this. The results for columns & attribute names can be cached with the Klass
			attrs = klass.allAttrs()
			attrs = [attr for attr in attrs if attr.hasSQLColumn()]
			colNames = [klass.sqlIdName()]
			colNames.extend([attr.sqlColumnName() for attr in attrs])
			className = klass.name()
			count = self.executeSQL('select %s from %s %s;' % (
				','.join(colNames), className, clauses))
			for row in self._cursor.fetchall():
				serialNum = row[0]
				key = ObjectKey().initFromClassNameAndSerialNum(className, serialNum)
				obj = self._objects.get(key, None)
				if obj is None:
					# Brand new object
					results = {}
					exec 'from %s import %s' % (className, className) in results
					pyClass = results[className]
					obj = pyClass()
					obj._mk_store = self
					# ^^^ a store is the only outsider that is allowed
					# to directly set a MiddleObject's store like this
					obj.initFromRow(row)
					obj.setKey(key)
					self._objects[key] = obj
				else:
					# Existing object
					obj.initFromRow(row)
				objs.append(obj)
		if isDeep:
			for klass in klass.subklasses():
				objs.extend(self.fetchObjectsOfClass(klass, clauses, isDeep))
		return objs


	## Klasses ##

	def klassForId(self, id):
		return self._klassesById[id]


	## Self utility ##

	def executeSQL(self, sql):
		''' Executes the given SQL, connecting to the database for the first time if necessary. This method will also log the SQL to self._sqlEcho, if it is not None. Returns whatever the DB API's cursor execute() method returns, which is undefined in DB API and varies from database to database (think hard before deciding to use it). '''
		if not self._connected:
			self.connect()
		self._sqlCount += 1
		if self._sqlEcho:
			timestamp = funcs.timestamp()['pretty']
			self._sqlEcho.write('SQL %03i. %s %s\n' % (self._sqlCount, timestamp, sql))
			self._sqlEcho.flush()
		return self._cursor.execute(sql.strip())

	def setSQLEcho(self, file):
		''' Sets a file to echo sql statements to, as sent through executeSQL(). None can be passed to turn echo off. '''
		self._sqlEcho = file


	## Obj refs ##

	def fetchObjRef(self, objRef):
		''' Given an unarchived object referece, this method returns the actual object for it (or None if the reference is NULL or dangling). While this method assumes that obj refs are stored as 64-bit numbers containing the class id and object serial number, subclasses are certainly able to override that assumption by overriding this method. '''
		assert type(objRef) is LongType, 'type=%r, objRef=%r' % (type(objRef), objRef)
		if objRef is None or objRef==0:
			return None
		else:
			klassId, serialNum = objRefSplit(objRef)
			if klassId==0 or serialNum==0:
				# invalid! we don't use 0 serial numbers
				return self.objRefZeroSerialNum(objRef)

			klass = self.klassForId(klassId)

			# Check if we already have this in memory first
			key = ObjectKey()
			key.initFromClassNameAndSerialNum(klass.name(), serialNum)
			obj = self._objects.get(key, None)
			if obj:
				return obj

			clauses = 'where %s=%d' % (klass.sqlIdName(), serialNum)
			objs = self.fetchObjectsOfClass(klass, clauses)
			if len(objs)>1:
				raise ValueError, 'Multiple objects.' # @@ 2000-11-22 ce: expand the msg with more information
			elif len(objs)==1:
				return objs[0]
			else:
				return self.objRefDangles(objRef)

	def objRefZeroSerialNum(self, objRef):
		''' Invoked by fetchObjRef() if either the class or object serial number is 0. '''
		self.warning('Zero serial number. Obj ref = %x.' % objRef)
		return None

	def objRefDangles(self, objRef):
		''' Invoked by fetchObjRef() if there is no possible target object for the given objRef, e.g., a dangling reference. This method invokes self.warning() and includes the objRef as decimal, hexadecimal and class:obj numbers. '''
		klassId, objSerialNum = objRefSplit(objRef)
		self.warning('Obj ref dangles. dec=%i  hex=%x  class:obj=%i:%i.' % (objRef, objRef, klassId, objSerialNum))
		return None


	## Debugging ##

	def dumpTables(self, out=None):
		if out is None:
			out = sys.stdout
		out.write('DUMPING TABLES\n')
		out.write('BEGIN\n')
		for klass in self.model().klasses().values():
			out.write(klass.name()+'\n')
			self.executeSQL('select * from %s;' % klass.name())
			out.write(str(self._cursor.fetchall()))
			out.write('\n')
		out.write('END\n')

	def dumpKlassIds(self, out=None):
		if out is None:
			out = sys.stdout
		wr = out.write('DUMPING KLASS IDs\n')
		for klass in self.model().klasses().values():
			out.write('%25s %2i\n' % (klass.name(), klass.id()))
		out.write('\n')


class MiddleObjectMixIn:

	def sqlObjRef(self):
		return objRefJoin(self.klass().id(), self.serialNum())

	def sqlInsertStmt(self):
		'''
		Returns the SQL insert statements for MySQL (as a tuple) in the form:
			insert into table (name, ...) values (value, ...);
		'''
		klass = self.klass()
		res = ['insert into %s (' % klass.name()]
		attrs = klass.allAttrs()
		attrs = [attr for attr in attrs if attr.hasSQLColumn()]
		fieldNames = [attr.sqlColumnName() for attr in attrs]
		if len(fieldNames)==0:
			fieldNames = [klass.sqlIdName()]
		res.append(','.join(fieldNames))
		res.append(') values (')
		values = [self.sqlValueForName(attr.name()) for attr in attrs]
		if len(values)==0:
			values = ['0']
		values = ','.join(values)
		res.append(values)
		res.append(');')
		return ''.join(res)

	def sqlUpdateStmt(self):
		'''
		Returns the SQL update statement for MySQL of the form:
			update table set name=value, ... where idName=idValue;
		Installed as a method of MiddleObject.
		'''
		assert self._mk_changedAttrs is not None
		assert len(self._mk_changedAttrs)>0
		klass = self.klass()
		assert klass is not None

		res = ['update %s set ' % klass.name()]
		for attr in self._mk_changedAttrs.values():
			colName = attr.sqlColumnName()
			res.append('%s=%s, ' % (colName, self.sqlValueForName(attr.name())))
		res[-1] = res[-1][:-2] + ' ' # e.g., shave off the trailing comma
		idValue = self.serialNum()
		res.append('where %s=%d;' % (klass.sqlIdName(), idValue))
		return ''.join(res)

	def sqlValueForName(self, name):
		# Our valueForKey() comes courtesy of MiscUtils.NamedValueAccess
		value = self.valueForKey(name)
		return self.klass().lookupAttr(name).sqlValue(value)

MixIn(MiddleObject, MiddleObjectMixIn)
	# Normally we don't have to invoke MixIn()--it's done automatically.
	# However, that only works when augmenting MiddleKit.Core classes
	# (MiddleObject belongs to MiddleKit.Run).


class Klass:

	def sqlIdName(self):
		name = self.name()
		return name[0].lower() + name[1:] + 'Id'


class Attr:

	def shouldRegisterChanges(self):
		''' Returns self.hasSQLColumn(). This only makes sense since there would be no point in registering changes on an attribute with no corresponding SQL column. The standard example of such an attribute is "list". '''
		return self.hasSQLColumn()

	def hasSQLColumn(self):
		''' Returns true if the attribute has a direct correlating SQL column in it's class' SQL table definition. Most attributes do. Those of type list do not. '''
		return 1

	def sqlColumnName(self):
		''' Returns the SQL column name corresponding to this attribute, consisting of self.name() + self.sqlTypeSuffix(). '''
		return self.name() + self.sqlTypeSuffix()

	def sqlTypeSuffix(self):
		''' Returns a string to be used as a suffix for sqlColumnName(). Returns an empty string. Occasionally, a subclass will override this to help clarify SQL column names of their type. '''
		return ''

	def sqlValue(self, value):
		''' For a given Python value, this returns the correct string for use in a SQL INSERT statement. Subclasses should override if this implementation, which returns repr(value), doesn't work for them. This method is responsible for returning 'NULL' if the value is None. '''
		if value is None:
			return 'NULL'
		else:
			return repr(value)


class LongAttr:

	def sqlValue(self, value):
		if value is None:
			return 'NULL'
		else:
			return str(value)


class ObjRefAttr:

	def sqlTypeSuffix(self):
		return 'Id'

	def sqlValue(self, value):
		if value is None:
			return 'NULL'
		else:
			assert type(value) is InstanceType
			assert isinstance(value, MiddleObject)
			value = value.sqlObjRef()
			return str(value)


class ListAttr:

	def hasSQLColumn(self):
		return 0


class AnyDateTimeAttr:

	def sqlValue(self, value):
		if value is None:
			return 'NULL'
		else:
			return "'%s'" % str(value)

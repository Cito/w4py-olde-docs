import sys, time
from types import InstanceType, LongType, StringType

from MiscUtils import NoDefault
from MiscUtils import Funcs as funcs

from MiddleObject import MiddleObject
from ObjectStore import ObjectStore, UnknownObjectError
from ObjectKey import ObjectKey
from MiscUtils.MixIn import MixIn
from MiddleKit.Core.ObjRefAttr import objRefJoin, objRefSplit

class SQLObjectStoreError(Exception): pass
class SQLObjectStoreThreadingError(SQLObjectStoreError): pass


class UnknownSerialNumberError(SQLObjectStoreError):
	'''
	For internal use when archiving objects.

	Sometimes an obj ref cannot be immediately resolved on INSERT because
	the target has not yet been inserted and therefore, given a serial number.
	'''
	def __init__(self, info):
		self.info = info

	def __repr__(self):
		return '%s: %s' % (self.__class__.__name__, self.info)

	def __str__(self):
		return str(self.info)


class UnknownSerialNumInfo:

	def updateStmt(self):
		assert self.sourceObject.serialNum!=0
		assert self.targetObject.serialNum()!=0
		return 'update %s set %s=%s where %s=%s;' % (
			self.tableName, self.fieldName, self.targetObject.sqlObjRef(), self.sqlIdName, self.sourceObject.serialNum())

	def __repr__(self):
		s = []
		for item in self.__dict__.items():
			s.append('%s=%r' % item)
		s = ' '.join(s)
		return '<%s %s>' % (self.__class__.__name__, s)


class SQLObjectStore(ObjectStore):
	'''
	TO DO:

		* _sqlEcho should be accessible via a config file setting as stdout, stderr or a filename.

	For details on DB API 2.0, including the thread safety levels see:
		http://www.python.org/topics/database/DatabaseAPI-2.0.html
	'''

	## Init ##

	def __init__(self, **kwargs):
		# @@ 2001-02-12 ce: We probably need a dictionary before kwargs for subclasses to pass to us in case they override __init__() and end up collecting kwargs themselves

		ObjectStore.__init__(self)
		self._dbArgs = kwargs
		self._connected = 0
		self._sqlEcho   = None
		self._sqlCount  = 0
		self._pyClassForName = {}   # cache. see corresponding method

	def modelWasSet(self):
		'''
		Performs additional set up of the store after the model is set,
		normally via setModel() or readModelFileNamed(). This includes
		checking that threading conditions are valid, and connecting to
		the database.
		'''
		ObjectStore.modelWasSet(self)

		# Check thread safety
		self._threaded = self.setting('Threaded')
		self._threadSafety = self.threadSafety()
		if self._threaded and self._threadSafety==0:
			raise SQLObjectStoreThreadingError, 'Threaded is 1, but the DB API threadsafety is 0.'

		# Cache some settings
		self._markDeletes = self.setting('DeleteBehavior', 'delete')=='mark'

		# Set up SQL echo
		self.setUpSQLEcho()

		# Connect
		self.connect()


	def setUpSQLEcho(self):
		'''
		Sets up the SQL echoing/logging for the store according to the
		setting 'SQLLog'. See the User's Guide for more info. Invoked by
		modelWasSet().
		'''
		setting = self.setting('SQLLog', None)
		if setting==None or setting=={}:
			self._sqlEcho = None
		else:
			filename = setting['File']
			if filename==None:
				self._sqlEcho = None
			elif filename=='stdout':
				self._sqlEcho = sys.stdout
			elif filename=='stderr':
				self._sqlEcho = sys.stderr
			else:
				mode = setting.get('Mode', 'write')
				assert mode in ['write', 'append']
				mode = mode[0]
				self._sqlEcho = open(filename, mode)


	## Connecting to the db ##

	def isConnected(self):
		return self._connected

	def connect(self):
		'''
		Connects to the database only if the store has not already and
		provided that the store has a valid model.

		The default implementation of connect() is usually sufficient
		provided that subclasses have implemented newConnection().
		'''
		assert self._model, 'Cannot connect: No model has been attached to this store yet.'
		if not self._connected:
			self._connection = self.newConnection()
			self._connected = 1
			self.readKlassIds()

	def newConnection(self):
		'''
		Returns a DB API 2.0 connection. This is a utility method
		invoked by connect(). Subclasses should implement this, making
		use of self._dbArgs (a dictionary specifying host, username,
		etc.) as well as self._model.sqlDatabaseName().

		Subclass responsibility.
		'''
		raise SubclassResponsibilityError

	def readKlassIds(self):
		'''
		Reads the klass ids from the SQL database. Invoked by connect().
		'
		'''
		conn, cur = self.executeSQL('select id, name from _MKClassIds;')
		klassesById = {}
		for (id, name) in cur.fetchall():
			assert id, "Id must be a non-zero int. id=%r, name=%r" % (id, name)
			klass = self._model.klass(name)
			klassesById[id] = klass
			klass.setId(id)
		self._klassesById = klassesById


	## Changes ##

	def commitInserts(self):
		unknownSerialNums = []
		for object in self._newObjects:
			self._insertObject(object, unknownSerialNums)

		for unknownInfo in unknownSerialNums:
			stmt = unknownInfo.updateStmt()
			self.executeSQL(stmt)
		self._newObjects = []

	def _insertObject(self, object, unknownSerialNums):
		# New objects not in the persistent store have serial numbers less than 1
		if object.serialNum()>0:
			try:
				rep = repr(object)
			except:
				rep = '(repr exception)'
			assert object.serialNum()<1, 'object=%s' % rep

		# SQL insert
		sql = object.sqlInsertStmt(unknownSerialNums)
		conn, cur = self.executeSQL(sql)

		# Get new id/serial num
		idNum = self.retrieveLastInsertId(conn, cur)

		# Update object
		object.setSerialNum(idNum)
		object.setKey(ObjectKey().initFromObject(object))
		object.setChanged(0)

		# Update our object pool
		self._objects[object.key()] = object

	def retrieveLastInsertId(self, conn, cur):
		''' Returns the id (typically a 32-bit int) of the last INSERT operation by this connection. Used by commitInserts() to get the correct serial number for the last inserted object.
		Subclass responsibility. '''
		raise SubclassResponsibilityError

	def commitUpdates(self):
		for object in self._changedObjects.values():
			sql = object.sqlUpdateStmt()
			self.executeSQL(sql)
		self._changedObjects.clear()

	def commitDeletions(self):
		for object in self._deletedObjects:
			sql = object.sqlDeleteStmt()
			self.executeSQL(sql)
		self._deletedObjects[:] = []


	## Fetching ##

	def fetchObject(self, aClass, serialNum, default=NoDefault):
		''' Fetches a single object of a specific class and serial number. TheClass can be a Klass object (from the MiddleKit object model), the name of the class (e.g., a string) or a Python class.
		Raises an exception if theClass parameter is invalid, or the object cannot be located.
		'''
		klass = self._klassForClass(aClass)
		objects = self.fetchObjectsOfClass(klass, serialNum=serialNum, isDeep=0)
		count = len(objects)
		if count==0:
			if default is NoDefault:
				raise UnknownObjectError, 'aClass = %r, serialNum = %r' % (aClass, serialNum)
			else:
				return default
		else:
			assert count==1
			return objects[0]

	def fetchObjectsOfClass(self, aClass, clauses='', isDeep=1, serialNum=None):
		'''
		Fetches a list of objects of a specific class. The list may be empty if no objects are found.
		aClass can be a Klass object (from the MiddleKit object model), the name of the class (e.g., a string) or a Python class.
		The clauses argument can be any SQL clauses such as 'where x<5 order by x'. Obviously, these could be specific to your SQL database, thereby making your code non-portable. Use your best judgement.
		serialNum can be a specific serial number if you are looking for a specific object.  If serialNum is provided, it overrides the clauses.
		You should label all arguments other than aClass:
			objs = store.fetchObjectsOfClass('Foo', clauses='where x<5')
		The reason for labeling is that this method is likely to undergo improvements in the future which could include additional arguments. No guarantees are made about the order of the arguments except that aClass will always be the first.
		Raises an exception if aClass parameter is invalid.
		'''
		klass = self._klassForClass(aClass)

		# Fetch objects of subclasses first, because the code below will be modifying clauses and serialNum
		deepObjs = []
		if isDeep:
			for subklass in klass.subklasses():
				deepObjs.extend(self.fetchObjectsOfClass(subklass, clauses, isDeep, serialNum))

		# Now get objects of this exact class
		objs = []
		if not klass.isAbstract():
			# @@ 2000-10-29 ce: Optimize this. The results for columns & attribute names can be cached with the Klass
			fetchSQLStart = klass.fetchSQLStart()
			className = klass.name()
			if serialNum is not None:
				clauses = 'where %s=%d' % (klass.sqlIdName(), serialNum)
			if self._markDeletes:
				clauses = self.addDeletedToClauses(clauses)
			conn, cur = self.executeSQL(fetchSQLStart + clauses + ';')
			for row in cur.fetchall():
				serialNum = row[0]
				key = ObjectKey().initFromClassNameAndSerialNum(className, serialNum)
				obj = self._objects.get(key, None)
				if obj is None:
					pyClass = self.pyClassForName(className)
					obj = pyClass()
					assert isinstance(obj, MiddleObject), 'Not a MiddleObject. obj = %r, type = %r, MiddleObject = %r' % (obj, type(obj), MiddleObject)
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
		objs.extend(deepObjs)
		return objs


	## Klasses ##

	def klassForId(self, id):
		return self._klassesById[id]


	## Self utility for SQL, connections, cursors, etc. ##

	def executeSQL(self, sql, connection=None):
		'''
		Executes the given SQL, connecting to the database for the first
		time if necessary. This method will also log the SQL to
		self._sqlEcho, if it is not None. Returns the connection and
		cursor used and relies on connectionAndCursor() to obtain these.
		Note that you can pass in a connection to force a particular one
		to be used.
		'''
		self._sqlCount += 1
		if self._sqlEcho:
			timestamp = funcs.timestamp()['pretty']
			self._sqlEcho.write('SQL %04i. %s %s\n' % (self._sqlCount, timestamp, sql))
			self._sqlEcho.flush()
		conn, cur = self.connectionAndCursor(connection)
		self._executeSQL(cur, sql.strip())
		return conn, cur

	def _executeSQL(self, cur, sql):
		"""
		Invokes execute on the cursor with the given SQL. This is a
		hook for subclasses that wish to influence this event. Invoked
		by executeSQL().
		"""
		cur.execute(sql)


	def setSQLEcho(self, file):
		''' Sets a file to echo sql statements to, as sent through executeSQL(). None can be passed to turn echo off. '''
		self._sqlEcho = file


	def connectionAndCursor(self, connection=None):
		'''
		Returns the connection and cursor needed for executing SQL,
		taking into account factors such as setting('Threaded') and the
		threadsafety level of the DB API module. You can pass in a
		connection to force a particular one to be used. Uses
		newConnection() and connect().
		'''
		if connection:
			conn = connection
		elif self._threaded:
			if self._threadSafety is 1:
				conn = self.newConnection()
			else: # safety = 2, 3
				if not self._connected:
					self.connect()
				conn = self._connection
		else:
			# Non-threaded
			if not self._connected:
				self.connect()
			conn = self._connection
		cursor = conn.cursor()
		return conn, cursor

	def newConnection(self):
		'''
		Subclasses must override to return the DB API module
		used by the subclass.
		'''
		raise SubclassResponsibilityError

	def threadSafety(self):
		return self.dbapiModule().threadsafety

	def addDeletedToClauses(self, clauses):
		'''
		Modify the given set of clauses so that it filters out records with non-NULL deleted field
		'''
		clauses = clauses.strip()
		if clauses.lower().startswith('where'):
			orderByIndex = clauses.lower().find('order by')
			if orderByIndex == -1:
				where = clauses[5:]
				orderBy = ''
			else:
				where = clauses[5:orderByIndex]
				orderBy = clauses[orderByIndex:]
			return 'where deleted is null and (%s) %s' % (where, orderBy)
		else:
			return 'where deleted is null %s' % clauses

	def pyClassForName(self, name):
		pyClass = self._pyClassForName.get(name, None)
		if pyClass is None:
			results = {}
			pkg = self._model.setting('Package', '')
			if pkg:
				pkg += '.'
			exec 'from %s%s import %s' % (pkg, name, name) in results
			pyClass = results[name]
			self._pyClassForName[name] = pyClass
		return pyClass

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
			objs = self.fetchObjectsOfClass(klass, clauses, isDeep=0)
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
		self.warning('Obj ref dangles. dec=%i  hex=%x  class.obj=%s.%i.' % (objRef, objRef, self.klassForId(klassId).name(), objSerialNum))
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


class Model:

	def sqlDatabaseName(self):
		# @@ 2001-06-15 ce: someday we might allow this to be set
		# or at least read from a config file
		return self.name()


class MiddleObjectMixIn:

	def sqlObjRef(self):
		return objRefJoin(self.klass().id(), self.serialNum())

	def sqlInsertStmt(self, unknowns):
		'''
		Returns the SQL insert statements for MySQL (as a tuple) in the form:
			insert into table (name, ...) values (value, ...);

		May add an info object to the unknowns list for obj references that
		are not yet resolved.
		'''
		klass = self.klass()
		res = ['insert into %s (' % klass.sqlTableName()]
		attrs = klass.allAttrs()
		attrs = [attr for attr in attrs if attr.hasSQLColumn()]
		fieldNames = [attr.sqlColumnName() for attr in attrs]
		if len(fieldNames)==0:
			fieldNames = [klass.sqlIdName()]
		res.append(','.join(fieldNames))
		res.append(') values (')
		values = []
		for attr in attrs:
			try:
				value = self.sqlValueForName(attr.name())
			except UnknownSerialNumberError, exc:
				exc.info.sourceObject = self
				unknowns.append(exc.info)
				value = 'NULL'
			values.append(value)
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

		res = ['update %s set ' % klass.sqlTableName()]
		for attr in self._mk_changedAttrs.values():
			colName = attr.sqlColumnName()
			res.append('%s=%s, ' % (colName, self.sqlValueForName(attr.name())))
		res[-1] = res[-1][:-2] + ' ' # e.g., shave off the trailing comma
		idValue = self.serialNum()
		res.append('where %s=%d;' % (klass.sqlIdName(), idValue))
		return ''.join(res)

	def sqlDeleteStmt(self):
		'''
		Returns the SQL delete statement for MySQL of the form:
			delete from table where idName=idValue;
		Or if deletion is being marked with a timestamp:
			update table set deleted=Now();
		Installed as a method of MiddleObject.
		'''
		klass = self.klass()
		assert klass is not None
		if self.store().model().setting('DeleteBehavior', 'delete') == 'mark':
			return 'update %s set deleted=Now() where %s=%d;' % (klass.sqlTableName(), klass.sqlIdName(), self.serialNum())
		else:
			return 'delete from %s where %s=%d;' % (klass.sqlTableName(), klass.sqlIdName(), self.serialNum())

	def referencingObjectsAndAttrsFetchKeywordArgs(self, backObjRefAttr):
		return {'clauses': 'WHERE %s=%s' % (backObjRefAttr.sqlColumnName(), self.sqlObjRef())}

	def sqlValueForName(self, name):
		# Our valueForKey() comes courtesy of MiscUtils.NamedValueAccess
		value = self.valueForKey(name)
		return self.klass().lookupAttr(name).sqlValue(value)

MixIn(MiddleObject, MiddleObjectMixIn)
	# Normally we don't have to invoke MixIn()--it's done automatically.
	# However, that only works when augmenting MiddleKit.Core classes
	# (MiddleObject belongs to MiddleKit.Run).


class Klass:

	_fetchSQLStart = None  # help out the caching mechanism in fetchSQLStart()

	def sqlTableName(self):
		'''
		Returns the name of the SQL table for this class.
		Returns self.name().
		Subclasses may wish to override to provide special quoting that
		prevents name collisions between table names and reserved words.
		'''
		return self.name()

	def sqlIdName(self):
		name = self.name()
		return name[0].lower() + name[1:] + 'Id'

	def fetchSQLStart(self):
		if self._fetchSQLStart is None:
			attrs = self.allAttrs()
			attrs = [attr for attr in attrs if attr.hasSQLColumn()]
			colNames = [self.sqlIdName()]
			colNames.extend([attr.sqlColumnName() for attr in attrs])
			self._fetchSQLStart = 'select %s from %s ' % (','.join(colNames), self.sqlTableName())
		return self._fetchSQLStart


class Attr:

	def shouldRegisterChanges(self):
		''' Returns self.hasSQLColumn(). This only makes sense since there would be no point in registering changes on an attribute with no corresponding SQL column. The standard example of such an attribute is "list". '''
		return self.hasSQLColumn()

	def hasSQLColumn(self):
		''' Returns true if the attribute has a direct correlating SQL column in it's class' SQL table definition. Most attributes do. Those of type list do not. '''
		return not self.get('isDerived', 0)

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


class IntAttr:

	def sqlValue(self, value):
		if value is None:
			return 'NULL'
		else:
			return str(value)
			# it's important to use str() since an int might
			# point to a long (whose repr() would be suffixed
			# with an 'L')


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
			if value.serialNum()==0:
				info = UnknownSerialNumInfo()
				info.tableName = self.klass().sqlTableName()
				info.fieldName = self.sqlColumnName()
				info.targetObject = value
				info.sqlIdName = self.klass().sqlIdName()
				raise UnknownSerialNumberError(info)
			else:
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
			# Chop off the milliseconds -- SQL databases seem to dislike that.
			return "'%s'" % str(value).split('.')[0]


class DateAttr:

	def sqlValue(self, value):
		if value is None:
			return 'NULL'
		else:
			# We often get "YYYY-MM-DD HH:MM:SS" from mx's DateTime
			# so we split on space and take the first value to
			# work around that.
			if 0:
				print
				print '>> type of value =', type(value)
				print '>> value = %r' % value
				print
			if type(value) is not StringType:
				value = str(value).split()[0]
			return "'%s'" % value

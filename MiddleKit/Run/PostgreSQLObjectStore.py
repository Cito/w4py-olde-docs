import sys
from SQLObjectStore import SQLObjectStore
from MiddleKit.Run.ObjectKey import ObjectKey
from MiddleObject import MiddleObject
from MiscUtils.MixIn import MixIn
import psycopg as dbi  # psycopg adapter; apt-get install python2.2-psycopg
from psycopg import Warning, DatabaseError
from SQLObjectStore import UnknownSerialNumberError
from MiscUtils import NoDefault

class PostgreSQLObjectStore(SQLObjectStore):
	"""
	PostgresObjectStore does the obvious: it implements an object store backed by a PostgreSQL database.

	The connection arguments passed to __init__ are:
		- host
		- user
		- passwd
		- port
		- unix_socket
		- client_flag

	You wouldn't use the 'db' argument, since that is determined by the model.
	"""

	def setting(self, name, default=NoDefault):
		# jdh: psycopg doesn't seem to work well with DBPool -- I've experienced
		# requests blocking indefinitely (deadlock?).  Besides, it does its
		# own connection pooling internally, so DBPool is unnecessary.
		if name == 'SQLConnectionPoolSize':
			return 0
		return SQLObjectStore.setting(self, name, default)

	def newConnection(self):
		args = self._dbArgs.copy()
		self.augmentDatabaseArgs(args)
		return self.dbapiModule().connect(**args)

	def augmentDatabaseArgs(self, args, pool=0):
		if not args.get('database'):
			args['database'] = self._model.sqlDatabaseName()

	def newCursorForConnection(self, conn, dictMode=0):
		return conn.cursor()
	
	def _insertObject(self, object, unknownSerialNums):
		# basically the same as the SQLObjectStore-
		# version but modified to retrieve the
		# serialNum via the oid (for which we need
		# class-name, unfortunately)
		object.klass
		seqname = "%s_%s_seq" % (object.klass().name(), object.klass().sqlSerialColumnName())
		conn, curs = self.executeSQL("select nextval('%s')" % seqname)
		id = curs.fetchone()[0]
		assert id, "Didn't get next id value from sequence"

		sql = object.sqlInsertStmt(unknownSerialNums,id=id)
		conn, curs = self.executeSQL(sql,conn)
		conn.commit()

		object.setSerialNum(id)
		object.setKey(ObjectKey().initFromObject(object))
		object.setChanged(0)

		self._objects[object.key()] = object

	def dbapiModule(self):
		return dbi

	def _executeSQL(self, cur, sql):
		try:
			cur.execute(sql)
		except Warning, e:
			if not self.setting('IgnoreSQLWarnings', 0):
				raise

	def saveChanges(self):
		conn, cur = self.connectionAndCursor()
		try:

			SQLObjectStore.saveChanges(self)
		except DatabaseError:
			conn.rollback()
			raise
		except Warning:
			if not self.setting('IgnoreSQLWarnings', 0):
				conn.rollback()
				raise
		conn.commit()

	def sqlCaseInsensitiveLike(self, a, b):
		return "%s ilike %s" % (a,b)


class Klass:

	def insertSQLStart(self):
		"""
		We override this so that the id column is always specified explicitly.
		"""
		if self._insertSQLStart is None:
			res = ['insert into %s (' % self.sqlTableName()]
			attrs = self.allDataAttrs()
			attrs = [attr for attr in attrs if attr.hasSQLColumn()]
			fieldNames = [self.sqlSerialColumnName()] + [attr.sqlColumnName() for attr in attrs]
			if len(fieldNames)==0:
				fieldNames = [self.sqlSerialColumnName()]
			res.append(','.join(fieldNames))
			res.append(') values (')
			self._insertSQLStart = ''.join(res)
			self._sqlAttrs = attrs
		return self._insertSQLStart, self._sqlAttrs

class MiddleObjectMixIn:


	def sqlInsertStmt(self, unknowns, id):
		"""
		We override this so that the id column is always specified explicitly.
		"""
		klass = self.klass()
		insertSQLStart, sqlAttrs = klass.insertSQLStart()
		values = []
		append = values.append
		extend = values.extend
		append(str(id))
		for attr in sqlAttrs:
			try:
				value = attr.sqlValue(self.valueForAttr(attr))
			except UnknownSerialNumberError, exc:
				exc.info.sourceObject = self
				unknowns.append(exc.info)
				value = 'NULL'
			if isinstance(value, str):
				append(value)
			else:
				extend(value) # value could be sequence for attrs that require multiple SQL columns
		if len(values)==0:
			values = ['0']
		values = ','.join(values)
		return insertSQLStart+values+');'

MixIn(MiddleObject, MiddleObjectMixIn)
	# Normally we don't have to invoke MixIn()--it's done automatically.
	# However, that only works when augmenting MiddleKit.Core classes
	# (MiddleObject belongs to MiddleKit.Run).

class StringAttr:
	def sqlForNonNone(self, value):
		""" psycopg provides a quoting function for string -- use it. """
		return "%s" % dbi.QuotedString(value)

class BoolAttr:
	def sqlForNonNone(self, value):
		if value:
			return 'TRUE'
		else:
			return 'FALSE'

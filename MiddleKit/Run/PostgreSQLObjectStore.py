import sys
from SQLObjectStore import SQLObjectStore
from MiddleKit.Run.ObjectKey import ObjectKey
import pgdb as dbi
from pgdb import Warning, DatabaseError

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

	def newConnection(self):
		args = self._dbArgs.copy()
		args['database'] = self._model.sqlDatabaseName()
		return self.dbapiModule().connect(**args)
	
	def _insertObject(self, object, unknownSerialNums):
		# basically the same as the SQLObjectStore-
		# version but modified to retrieve the
		# serialNum via the oid (for which we need
		# class-name, unfortunately)
		sql = object.sqlInsertStmt(unknownSerialNums)
		conn, curs = self.executeSQL(sql)

		oid = curs.lastoid()
		className = object.__class__.__name__
		curs.execute("select %s from %s where oid=%d" %
			( className + "id", className, oid ) )
		conn.commit()

		object.setSerialNum(curs.fetchone()[0])
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

		sys.stderr.write("Committing changes\n")
		conn.commit()

# Mixins

class StringAttr:
	def sqlValue(self, value):
		# Postgres provides a quoting function for string -- use it.
		if value is None:
			return 'NULL'
		else:
			return str(dbi._quote(value))

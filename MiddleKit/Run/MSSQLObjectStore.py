#import SQLObjectStore
#reload (SQLObjectStore)
from SQLObjectStore import SQLObjectStore
import ODBC.Windows

class MSSQLObjectStore(SQLObjectStore):
	'''
	MSSQLObjectStore does the obvious: it implements an object store backed by a MSSQL database.

	The connection arguments passed to __init__ are:
		- host
		- user
		- passwd
		- port
		- unix_socket
		- client_flag

	You wouldn't use the 'db' argument, since that is determined by the model.
	'''

	def dbapiConnect(self):
		'''
		Returns a DB API 2.0 connection. This is a utility method invoked by connect(). Subclasses should implement this, making use of self._dbArgs (a dictionary specifying host, username, etc.).
		Subclass responsibility.
		MSSQL 2000 defaults to autocommit ON (at least mine does)
		if you want it off, do not send any arg for clear_auto_commit or set it to 1
		# self._db = ODBC.Windows.Connect(dsn='myDSN',clear_auto_commit=0)
		'''
		return apply(ODBC.Windows.Connect, (), self._dbArgs)

	def retrieveLastInsertId(self):
		query = 'select @@IDENTITY'
		result = self.executeSQL(query)
		return int(self._cursor.fetchone()[0])


class Klass:

	def sqlTableName(self):
		'''
		Returns "[name]" so that table names do not conflict with SQL
		reserved words.
		'''
		return '[%s]' % self.sqlTableName()


class StringAttr:

	def sqlValue(self, value):
		if value is None:
			return 'NULL'
		else:
			# do the right thing
			value = value.replace("'","''")
			return "'" + value + "'"

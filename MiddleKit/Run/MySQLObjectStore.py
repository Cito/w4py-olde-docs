from SQLObjectStore import SQLObjectStore
import MySQLdb


class MySQLObjectStore(SQLObjectStore):
	'''
	MySQLObjectStore does the obvious: it implements an object store backed by a MySQL database.

	MySQL notes:
		* MySQL home page: http://www.mysql.com.
		* MySQL version this was developed and tested with: 3.22.34 & 3.23.27
		* The platforms developed and tested with include Linux (Mandrake 7.1) and Windows ME.
		* The MySQL-Python DB API 2.0 module used under the hood is MySQLdb by Andy Dustman. http://dustman.net/andy/python/MySQLdb/

	The connection arguments passed to __init__ are:
		- host
		- user
		- passwd
		- port
		- unix_socket
		- client_flag

	You wouldn't use the 'db' argument, since that is determined by the model.

	See the MySQLdb docs or the DB API 2.0 docs for more information.
	  http://www.python.org/topics/database/DatabaseAPI-2.0.html
	'''

	def newConnection(self):
		return self.dbapiModule().connect(**self._dbArgs)

	def retrieveLastInsertId(self):
		conn, cur = self.executeSQL('select last_insert_id();')
		# @@ 2001-05-23 ce: there is a specific Python call for this in MySQLdb that we should try
		return cur.fetchone()[0]

	def dbapiModule(self):
		return MySQLdb


# Mixins

class StringAttr:
	def sqlValue(self, value):
		""" MySQL provides a quoting function for string -- use it. """
		if value is None:
			return 'NULL'
		else:
			return "'" + MySQLdb.escape_string(value) + "'"


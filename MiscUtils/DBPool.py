'''
DBPool.py

Implements a pool of cached connections to a database. This should result in a speedup for persistent apps.

The pool of connections is threadsafe regardless of whether the DB API module question in general has a threadsafety of 1 or 2.

Reportedly there has been no speed up in tests with MySQL.

For more information on the DB API, see:
	http://www.python.org/topics/database/DatabaseAPI-2.0.html


FUTURE

* If in the presence of WebKit, register ourselves as a Can.


CREDIT

* Contributed by Dan Green
* thread safety bug found by Tom Schwaller
* Fixes by Geoff Talvola (thread safety in _threadsafe_getConnection()).
* Clean up by Chuck Esterbrook.
'''


import threading


class DBPoolError(Exception): pass
class UnsupportedError(DBPoolError): pass


class PooledConnection:
	''' A wrapper for database connections to help with DBPool. You don't normally deal with this class directly, but use DBPool to get new connections. '''

	def __init__(self, pool, con):
		self._con = con
		self._pool = pool

	def close(self):
		if self._con!=None:
			self._pool.returnConnection(self._con)
			self._con = None

	def __getattr__(self, name):
		return getattr(self._con, name)

	def __del__(self):
		self.close()


class DBPool:

	def __init__(self, dbModule, maxConnections, *args, **kwargs):
		if dbModule.threadsafety==0:
			raise UnsupportedError, "Database module does not support any level of threading."
		elif dbModule.threadsafety==1:
			from Queue import Queue
			self._queue = Queue(maxConnections)
			self.addConnection = self._unthreadsafe_addConnection
			self.getConnection = self._unthreadsafe_getConnection
			self.returnConnection = self._unthreadsafe_addConnection
		elif dbModule.threadsafety>=2:
			self._lock = threading.Lock()
			self._nextCon = 0
			self._connections = []
			self.addConnection = self._threadsafe_addConnection
			self.getConnection = self._threadsafe_getConnection
			self.returnConnection = self._threadsafe_returnConnection

		# @@ 2000-12-04 ce: Should we really make all the connections now?
		# Couldn't we do this on demand?
		for i in range(maxConnections):
			con = apply(dbModule.connect, args, kwargs)
			self.addConnection(con)


	# threadsafe/unthreadsafe refers to the database _module_, not THIS class..
	# this class is definitely threadsafe (um. that is, I hope so - Dan)

	def _threadsafe_addConnection(self, con):
		self._connections.append(con)


	def _threadsafe_getConnection(self):
		self._lock.acquire()
		try:
			con = PooledConnection(self, self._connections[self._nextCon])
			self._nextCon = self._nextCon + 1
			if self._nextCon >= len(self._connections):
				self._nextCon = 0
			return con
		finally:
			self._lock.release()

	def _threadsafe_returnConnection(self, con):
		return

	# We'd MUCH rather use the other versions, but oh well..
	def _unthreadsafe_addConnection(self, con):
		self._queue.put(con)

	def _unthreadsafe_getConnection(self):
		return PooledConnection(self, self._queue.get())

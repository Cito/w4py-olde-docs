from SessionStore import SessionStore


class SessionMemoryStore(SessionStore):
	'''
	Stores the session in memory as a dictionary.

	This is fast and secure when you have one, persistent app server.
	'''


	## Init ##

	def __init__(self, app):
		SessionStore.__init__(self, app)
		self._store = {}


	## Access ##

	def __len__(self):
		return len(self._store)

	def __getitem__(self, key):
		return self._store[key]

	def __setitem__(self, key, item):
		self._store[key] = item

	def __delitem__(self, key):
		del self._store[key]

	def has_key(self, key):
		return self._store.has_key(key)

	def keys(self):
		return self._store.keys()

	def clear(self):
		self._store.clear()

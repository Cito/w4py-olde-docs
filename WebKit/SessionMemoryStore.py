from SessionStore import SessionStore
from SessionFileStore import SessionFileStore
import os


class SessionMemoryStore(SessionStore):
	'''
	Stores the session in memory as a dictionary.

	This is fast and secure when you have one, persistent app server.
	'''


	## Init ##

	def __init__(self, app, restoreFiles=1):
		SessionStore.__init__(self, app)
		self._store = {}
		if self._app.server().isPersistent() and restoreFiles == 1:
			filestore = SessionFileStore(app)
			keys = filestore.keys()
			for i in keys:
				self[i] = filestore[i]



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


	## Application support ##

	def storeSession(self, session):
		pass

	def storeAllSessions(self):
		print "Storing Sessions to file.\n"
		if self._app.server().isPersistent():
			filestore = SessionFileStore(self._app)
			for i in self.keys():
				filestore[i]=self[i]

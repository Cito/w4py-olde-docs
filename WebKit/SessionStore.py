from Common import *


class SessionStore(Object):
	'''
	SessionStores are dictionary-like objects used by Application to store session state. This class is abstract and it's up to the concrete subclass to implement several key methods that determine how sessions are stored (such as in memory, on disk or in a database).

	Subclasses may rely on the attribute self._app to point to the application.

	Subclasses should be named SessionFooStore since Application expects "Foo" to appear for the "SessionStore" setting and automatically prepends Session and appends Store. Currently, you will also need to add another import statement in Application.py. Search for SessionStore and you'll find the place.

	TO DO

	* Should there be a check-in/check-out strategy for sessions to prevent concurrent requests on the same session? If so, that can probably be done at this level (as opposed to pushing the burden on various subclasses).
	'''


	## Init ##

	def __init__(self, app):
		''' Subclasses must invoke super. '''
		Object.__init__(self)
		self._app = app


	## Access ##

	def application(self):
		return self._app


	## Dictionary-style access ##

	def __len__(self):
		raise SubclassResponsibilityError

	def __getitem__(self, key):
		raise SubclassResponsibilityError

	def __setitem__(self, key, item):
		raise SubclassResponsibilityError

	def __delitem__(self, key):
		raise SubclassResponsibilityError

	def has_key(self, key):
		raise SubclassResponsibilityError

	def keys(self):
		raise SubclassResponsibilityError

	def clear(self):
		raise SubclassResponsibilityError


	## Convenience methods ##

	def items(self):
		items = map(lambda key, self=self: (key, self[key]), self.keys())

	def values(self):
		values = map(lambda key, self=self: self[key], self.keys())

	def get(self, key, default=None):
		if self.has_key(key):
			return self[key]
		else:
			return default


	## As a string ##

	def __repr__(self):
		d = {}
		d.update(self)
		return repr(d)

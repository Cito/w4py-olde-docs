#
# JSON-RPC servlet class written by Jean-Francois Pieronne
#

import traceback
from MiscUtils import StringIO
try:
	import simplejson
except ImportError:
	print "ERROR: simplejson is not installed."
	print "Get it from http://cheeseshop.python.org/pypi/simplejson"

from HTTPContent import HTTPContent


class JSONRPCServlet(HTTPContent):
	"""A superclass for Webware servlets using JSON-RPC techniques.

	JSONRPCServlet can be used to make coding JSON-RPC applications easier.

	Subclasses should override the method json_methods() which returns a list
	of method names. These method names refer to Webware Servlet methods that
	are able to be called by an JSON-RPC-enabled web page. This is very similar
	in functionality to Webware's actions.

	"""

	# Class level variables that can be overridden by servlet instances:
	_debug = 0 # set to True if you want to see debugging output
	_allowGet = 0 # set to True if you want to allow GET requests

	def __init__(self):
		HTTPContent.__init__(self)

	def respondToGet(self, transaction):
		"""Deny GET requests with JSON by returning an error.

		This forces clients to use POST requests only, since GET requests
		with JSON are vulnerable to "JavaScript hijacking".

		"""
		if not self._allowGet:
			self.error("GET method not allowed")
		HTTPContent.respondToGet(self, transaction)

	def defaultAction(self):
		self.json_call()

	def actions(self):
		actions = HTTPContent.actions(self)
		actions.append('json_call')
		return actions

	def json_methods(self):
		return []

	def json_call(self):
		"""Execute method with arguments on the server side.

		Returns Javascript function to be executed by the client immediately.

		"""
		request = self.request()
		data = simplejson.loads(request.rawInput().read())
		id, call, params = data["id"], data["method"], data["params"]
		self._id = id
		if call == 'system.listMethods':
			result = self.json_methods()
			self.write(simplejson.dumps({'id': id, 'result': result}))
		elif call in self.json_methods():
			try:
				method = getattr(self, call)
			except AttributeError:
				self.error('%s, although an approved method, '
					'was not found' % call)
			else:
				try:
					if self._debug:
						self.log("json call %s(%s)" % (call, params))
					result = method(*params)
					self.write(simplejson.dumps({'id': id, 'result': result}))
				except Exception:
					err = StringIO()
					traceback.print_exc(file=err)
					e = err.getvalue()
					self.error('%s was called, '
						'but encountered an error: %s' % (call, e))
					err.close()
		else:
			self.error('%s is not an approved method' % call)

	def error(self, msg):
		self.write(simplejson.dumps({'id': self._id, 'code': -1, 'error': msg}))

#
# JSON-RPC servlet class written by Jean-Francois Pieronne
#

import traceback
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO
try:
    import simplejson
except ImportError:
    print "ERROR: simplejson is not installed."
    print "Get it from http://cheeseshop.python.org/pypi/simplejson"

from WebKit.HTTPContent import HTTPContent

debug = 0

class JSONRPCServlet(HTTPContent):
	"""A superclass for Webware servlets using JSON-RPC techniques.

	JSONRPCServlet can be used to make coding JSON-RPC applications easier.

	Subclasses should override the method json_methods() which returns a list
	of method names. These method names refer to Webware Servlet methods that
	are able to be called by an JSON-RPC-enabled web page. This is very similar
	in functionality to Webware's actions.

	"""

	def __init__(self):
		HTTPContent.__init__(self)

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
		self.id = id
		if call == 'system.listMethods':
			result = self.json_methods()
			self.write(simplejson.dumps({'id': id, 'result': result}))
		elif call in self.json_methods():
			try:
				method = getattr(self, call)
			except AttributeError:
				cmd = self.error('%s, although an approved method,'
					' was not found' % call)
			else:
				try:
					if debug:
						self.log("json call %s(%s)" % (call, params))
					result = method(*params)
					self.write(simplejson.dumps({'id': id, 'result': result}))
				except Exception:
					err = StringIO()
					traceback.print_exc(file=err)
					e = err.getvalue()
					cmd = self.error('%s was called,'
						' but encountered an error: %s' % (call, e))
					err.close()
		else:
			self.error('%s is not an approved method' % call)

	def error(self, msg):
		self.write(simplejson.dumps({'id': self.id, 'code': -1, 'error': msg}))

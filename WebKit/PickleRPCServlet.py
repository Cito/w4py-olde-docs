from RPCServlet import RPCServlet
import sys, traceback, types
from time import time
from MiscUtils.PickleRPC import RequestError
try:
	from cPickle import dumps, load
except ImportError:
	from pickle import dumps, load


class PickleRPCServlet(RPCServlet):
	"""
	PickleRPCServlet is a base class for Dict-RPC servlets.

	The "Pickle" refers to Python's pickle module. This class is
	similar to XMLRPCServlet. By using Python pickles you get their
	convenience (assuming the client is Pythonic), but lose
	language independence. Some of us don't mind that last one.  ;-)

	Conveniences over XML-RPC include the use of all of the following:
	  * Any pickle-able Python type (mx.DateTime for example)
	  * Python instances (aka objects)
	  * None
	  * Longs that are outside the 32-bit int boundaries
	  * Keyword arguments

	Pickles should also be faster than XML.

	One possible drawback is security. See MiscUtils.PickleRPC for more
	details.

	To make your own PickleRPCServlet, create a subclass and implement a
	method which is then named in exposedMethods():

		from WebKit.PickleRPCServlet import PickleRPCServlet
		class Math(PickleRPCServlet):
			def multiply(self, x, y):
				return x * y
			def exposedMethods(self):
				return ['multiply']

	To make a PickleRPC call from another Python program, do this:
		from MiscUtils.PickleRPC import Server
		server = Server('http://localhost/WebKit.cgi/Context/Math')
		print server.multiply(3, 4)    # 12
		print server.multiply('-', 10) # ----------

	If a request error is raised by the server, then
	MiscUtils.PickleRPC.RequestError is raised. If an unhandled
	exception is raised by the server, or the server response is
	malformed, then	MiscUtils.PickleRPC.ResponseError (or one of
	it's subclasses) is raised.

	Tip: If you want callers of the RPC servlets to be able to
	introspect what methods are available, then include
	'exposedMethods' in exposedMethods().

	If you wanted the actual response dictionary for some reason:
		print server._request('multiply', 3, 4)
			# { 'value': 12, 'timeReceived': ... }

	In which case, an exception is not purposefully raised if the
	dictionary contains	one. Instead, examine the dictionary.

	For the dictionary formats and more information see the docs
	for MiscUtils.PickleRPC.

	TO DO

	* Geoff T mentioned that security concerns were mentioned when
	  pickling was discussed before. What are they?
	"""

	def respondToPost(self, trans):
		transReponse = trans.response()
		try:
			data = trans.request().dictInput()
			response = {
				'timeReceived': trans.request().time(),
			}
			try:
				try:
					req = load(data)
				except:
					raise RequestError, 'Cannot unpickle dict-rpc request.'
				if not isinstance(req, types.DictType):
					raise RequestError, 'Expecting a dictionary for dict-rpc requests, but got %s instead.' % type(dict)
				if req.get('version', 1)!=1:
					raise RequestError, 'Cannot handle version %s requests.' % req['version']
				if req.get('action', 'call')!='call':
					raise RequestError, 'Cannot handle the request action, %r.' % req['action']
				try:
					methodName = req['methodName']
				except KeyError:
					raise RequestError, 'Missing method in request'
				args = req.get('args', ())
				if methodName=='__methods__.__getitem__':
					# support PythonWin autoname completion
					response = self.exposedMethods()[args[0]]
				else:
					response['value'] = self.call(methodName, *args, **req.get('keywords', {}))
			except RequestError, e:
				response['requestError'] = str(e)
			except Exception, e:
				response['exception'] = self.resultForException(e, trans)
			response['timeResponded'] = time()
			response = dumps(response)
		except:
			# internal error, report as HTTP server error
			print 'PickleRPCServlet internal error'
			print ''.join(traceback.format_exception(*sys.exc_info()))
			trans.response().setStatus(500, 'Server Error')
		else:
			self.sendOK('text/python/pickle/dict', response, trans)

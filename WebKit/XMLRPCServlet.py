# This requires the free xml-rpc library available from
# http://www.pythonware.com/products/xmlrpc/
#
# See Examples/XMLRPCExample.py for sample usage.
#

import sys, xmlrpclib
from HTTPServlet import HTTPServlet

class XMLRPCServlet(HTTPServlet):
	'''
	XMLRPCServlet is a base class for XML-RPC servlets.
	See Examples/XMLRPCExample.py for sample usage.	
	'''
	def respondToPost(self, transaction):
		'''
		This is similar to the xmlrpcserver.py example from the xmlrpc
		library distribution, only it's been adapted to work within a
		WebKit servlet.
		'''
		try:
			# get arguments
			data = transaction.request().rawRequest()['input']
			params, method = xmlrpclib.loads(data)

			# generate response
			try:
				response = self.call(method, params)
				if type(response) != type(()):
					response = (response,)
			except:
				# report exception back to server
				response = xmlrpclib.dumps(
					xmlrpclib.Fault(1, "%s:%s" % (sys.exc_type, sys.exc_value))
					)
			else:
				response = xmlrpclib.dumps(
					response,
					methodresponse=1
					)
		except:
			# internal error, report as HTTP server error
			transaction.response().setHeader('Status', 500)
		else:
			# got a valid XML RPC response
			transaction.response().setHeader('Status', 200)
			transaction.response().setHeader("Content-type", "text/xml")
			transaction.response().setHeader("Content-length", str(len(response)))
			transaction.response().write(response)

	def call(self, method, params):
		'''
		Subclasses may override this class for custom handling of methods.
		'''
		if method in self.exposedMethods():
			return apply(getattr(self, method), params)
		else:
			raise 'method not implemented', method

	def exposedMethods(self):
		'''
		Subclasses should return a list of methods that will be exposed through XML-RPC.
		'''
		return []

# This requires the free xml-rpc library available from
# http://www.pythonware.com/products/xmlrpc/
#
# See Examples/XMLRPCExample.py for sample usage.
#

import sys, xmlrpclib, string, traceback
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
			data = transaction.request().xmlInput().read()
			params, method = xmlrpclib.loads(data)

			# generate response
			try:
				if method == '__methods__.__getitem__':
					response = self.exposedMethods()[params[0]]
				else:
					response = self.call(method, params)
				if type(response) != type(()):
					response = (response,)
			except:
				# report exception back to server
				if transaction.application().setting('IncludeTracebackInXMLRPCFault', 0):
					fault = string.join(traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2]))
				else:
					fault = 'unhandled exception'
				response = xmlrpclib.dumps(xmlrpclib.Fault(1, fault))
			else:
				response = xmlrpclib.dumps(response, methodresponse=1)
		except:
			# internal error, report as HTTP server error
			transaction.response().setStatus(500, 'Server Error')
		else:
			# got a valid XML RPC response
			transaction.response().setStatus(200, 'OK')
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

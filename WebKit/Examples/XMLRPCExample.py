from WebKit.XMLRPCServlet import XMLRPCServlet
import operator

class XMLRPCExample(XMLRPCServlet):
	'''
	Example XML-RPC servlet.  To try it out, use something like the following:

	>>> import xmlrpclib
	>>> server = xmlrpclib.Server('http://localhost/cgi-bin/WebKit.cgi/Examples/XMLRPCExample')
	>>> server.multiply(10,20,30)
	6000
	>>> server.add(10,20,30)
	60

	You'll get an exception if you try to call divide, because that
	method is not listed in exposedMethods.
	'''
	
	def exposedMethods(self):
		return ['multiply', 'add']

	def multiply(self, *args):
		return reduce(operator.mul, args)

	def add(self, *args):
		return reduce(operator.add, args)

	def divide(self, *args):
		return reduce(operator.div, args)


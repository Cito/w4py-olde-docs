from Common import *
from Servlet import Servlet


class HTTPServlet(Servlet):
	'''
	HTTPServlet implements the respond() method to invoke methods such as respondToGet() and respondToPut() depending on the type of HTTP request.
	Current supported request are GET, POST, PUT, DELETE, OPTIONS and TRACE.
	The dictionary _map contains the information about the types of requests and their corresponding methods.
	
	Note that HTTPServlet inherits awake() and respond() methods from Servlet and that subclasses may make use of these.
	
	See also: Servlet

	FUTURE
		* Document methods (take hints from Java HTTPServlet documentation)
	'''
	
	## Init ##
	
	def __init__(self):
		Servlet.__init__(self)
		self._map = {
			'GET':     self.respondToGet,
			'POST':    self.respondToPost,
			'PUT':     self.respondToPut,
			'DELETE':  self.respondToDelete,
			'OPTIONS': self.respondToOptions,
			'TRACE':   self.respondToTrace
		}


	## Transactions ##
	
	def respond(self, trans):
		''' Invokes the appropriate respondToSomething() method depending on the type of request (e.g., GET, POST, PUT, ...). '''
		method = self._map[trans.request().method()]
		method(trans)
	
	def respondToGet(self, trans):
		raise SubclassResponsibilityError
	
	def respondToPost(self, trans):
		raise SubclassResponsibilityError

	def respondToPut(self, trans):
		raise SubclassResponsibilityError
	
	def respondToDelete(self, trans):
		raise SubclassResponsibilityError
	
	def respondToOptions(self, trans):
		raise SubclassResponsibilityError
	
	def respondToTrace(self, trans):
		raise SubclassResponsibilityError

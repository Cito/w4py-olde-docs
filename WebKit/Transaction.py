from Common import *


class Transaction(Object):
	'''
	A transaction is a container for the transactionual information of a transaction. This includes the application, request, response and session. It also includes the initial servlet for which the request was made and the current servlet executing in the case of nested servlets.
	'''

	## Init ##
	
	def __init__(self, application, request=None):
		Object.__init__(self)
		self._application   = application
		self._request       = request
		self._response      = None
		self._session       = None
		self._servlet       = None
		self._errorOccurred = 0
	

	## Access ##
	
	def application(self):
		return self._application

	def request(self):
		return self._request
	
	def response(self):
		return self._response
		
	def setResponse(self, response):
		self._response = response

	def session(self):
		if not self._session:
			self._session = self._application.createSessionForTransaction(self)
		return self._session
	
	def setSession(self, session):
		self._session = session

	def servlet(self):
		''' Return the current servlet that is processing. Remember that servlets can be nested. '''
		#print ">> Someone asked for the servlet"
		return self._servlet

	def setServlet(self, servlet):
		self._servlet = servlet

	def duration(self):
		''' Returns the duration, in seconds, of the transaction (basically response end time minus request start time). '''
		return self._response.endTime() - self._request.time()

	def errorOccurred(self):
		return self._errorOccurred

	def setErrorOccurred(self, flag):
		''' Invoked by the application if an exception is raised to the application level. '''
		self._errorOccurred = flag
		self._servlet=None

		
	## Debugging ##
	
	def dump(self, f=sys.stdout):
		''' Dumps debugging info to stdout. '''
		f.write('>> Transaction: %s\n' % self)
		for attr in dir(self):
			f.write('%s: %s\n' % (attr, getattr(self, attr)))
		f.write('\n')

		
	## Die ##
	
	def die(self):
		''' This method should be invoked when the entire transaction is finished with. Currently, this is invoked by AppServer. This method removes references to the different objects in the transaction, breaking cyclic reference chains and allowing Python to collect garbage. '''		

		
		from types import InstanceType
		for attrName in dir(self):
			# @@ 2000-05-21 ce: there's got to be a better way!
			attr = getattr(self, attrName)
			if type(attr) is InstanceType and hasattr(attr, 'resetKeyBindings'):
				#print '>> resetting'
				attr.resetKeyBindings()
			delattr(self, attrName)




from Common import *


class Servlet(Object):
	'''
	A servlet is a key portion of a server-based application that implements the semantics of a particular request by providing a response.
	This abstract class defines servlets at a very high level. Most often, developers will subclass HTTPServlet or even Page.
	Servlets can be created once, then used and destroyed, or they may be reused several times over (it's up to the server). Therefore, servlet developers should take the proper actions in awake() and sleep() so that reuse can occur.

	Objects that participate in a transaction include:
		* Application
		* Request
		* Transaction
		* Session
		* Servlet
		* Response

	The awake(), respond() and sleep() methods form a message sandwich. Each is passed an instance of Transaction which gives further access to all the objects involved.
	'''

	## Init ##

	def __init__(self):
		''' Subclasses must invoke super. '''
		Object.__init__(self)
		self._serverSidePath = None
		self._serverSideDir = None
		self._session = None


	## Access ##

	def name(self):
		''' Returns the name which is simple the name of the class. Subclasses should *not* override this method. It is used for logging and debugging. '''
		return self.__class__.__name__


	## Request-response cycles ##

	def awake(self, trans):
		''' This message is sent to all objects that participate in the request-response cycle in a top-down fashion, prior to respond(). Subclasses must invoke super. '''
		pass

	def respond(self, trans):
		raise SubclassResponsibilityError

	def sleep(self, trans):
		pass


	## Log ##

	def log(self, message):
		''' This can be invoked to print messages concerning the servlet. This is often used by self to relay important information back to developers. '''
		print '[%s] [msg] %s' % (asclocaltime(), message)


	## Abilities ##

	def canBeThreaded(self):
		''' Returns 0 or 1 to indicate if the servlet can be multithreaded. This value should not change during the lifetime of the object. The default implementation returns 0. Note: This is not currently used. '''
		return 0

	def canBeReused(self):
		''' Returns 0 or 1 to indicate if a single servlet instance can be reused. The default is 1, but subclasses con override to return 0. Keep in mind that performance may seriously be degraded if instances can't be reused. Also, there's no known good reasons not to reuse and instance. Remember the awake() and sleep() methods are invoked for every transaction. But just in case, your servlet can refuse to be reused. '''
		return 1


	## Cans ##

	def getCan(self, ID, klass, storage,trans,*args, **kargs):
		""" Gets a Can, but requires that the transaction be passed in."""
		storage = string.lower(storage)
		if storage=="session":
			container=trans.session()
		elif storage=="request":
			container=trans.request()
		elif storage=="application":
			container=trans.application()
		else:
			print storage
			raise "Invalid Storage Parameter",storage

		instance = container.getCan(ID)
		if instance == None:
			instance = apply(trans.application()._canFactory.createCan,(klass,)+args,kargs)
			container.setCan(ID,instance)
		return instance


	## Server side filesystem ##

	def serverSideDir(self):
		''' Returns the filesytem directory of the page on the server. '''
		if self._serverSideDir is None:
			self._serverSideDir = os.path.dirname(self._request.serverSidePath())
		return self._serverSideDir

	def serverSidePath(self):
		''' Returns the filesystem path of the page on the server. '''
		if self._serverSidePath is None:
			self._serverSidePath = self._request.serverSidePath()
		return self._serverSidePath

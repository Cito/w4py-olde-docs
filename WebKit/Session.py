from Common import *
import whrandom
from time import localtime, time
from CanContainer import *



class SessionError(Exception):
	pass


class Session(Object, CanContainer):
	'''
	All methods that deal with time stamps, such as creationTime(),
	treat time as the number of seconds since January 1, 1970.

	Session identifiers are stored in cookies. Therefore, clients
	must have cookies enabled.

	Unlike Response and Request, which have HTTP subclass versions
	(e.g., HTTPRequest and HTTPResponse respectively), Session does
	not. This is because there is nothing protocol specific in
	Session. (Is that true considering cookies? @@ 2000-04-09 ce)
	2000-04-27 ce: With regards to ids/cookies, maybe the notion
	of a session id should be part of the interface of a Request.

	Note that the session id should be a string that is valid
	as part of a filename. This is currently true, and should
	be maintained if the session id generation technique is
	modified. Session ids can be used in filenames.

	FUTURE

		* invalidate()
		* Sessions don't actually time out and invalidate themselves.
		* Should this be called 'HTTPSession'?
		* Should "numTransactions" be exposed as a method? Should it be common to all transaction objects that do the awake()-respond()-sleep() thing? And should there be an abstract super class to codify that?
	'''

	## Init ##

	def __init__(self, trans):
		Object.__init__(self)
		self._maxIdleInterval = 0
		self._lastAccessTime  = self._creationTime = time()
		self._numTrans        = 0
		self._values          = {}

		attempts = 0
		while attempts<10000:
			self._identifier = string.join(map(lambda x: '%02d' % x, localtime(time())[:6]), '') + str(whrandom.whrandom().randint(10000, 99999))
			if not trans.application().hasSession(self._identifier):
				break
			attempts = attempts + 1
		else:
			raise SessionError, "Can't create valid session id after %d attempts." % attempts


	## Access ##

	def creationTime(self):
		''' Returns the time when this session was created. '''
		return self._creationTime

	def lastAccessTime(self):
		''' Returns the last time the user accessed the session through interaction. This attribute is updated in awake(), which is invoked at the beginning of a transaction. '''
		return self._lastAccessTime

	def maxIdleInterval(self):
		return self._maxIdleInterval

	def setMaxIdleInterval(self, seconds):
		self._maxIdleInterval = seconds

	def identifier(self):
		''' Returns a string that uniquely identifies the session. This method will create the identifier if needed. '''
		return self._identifier

	def isNew(self):
		return self._numTrans<2


	## Invalidate ##

	def invalidate(self):
		''' Invalidates the session. @@ 2000-05-09 ce: Not implemented. '''
		raise NotImplementedError


	## Values ##

	def value(self, name, default=Tombstone):
		if default is Tombstone:
			return self._values[name]
		else:
			return self._values.get(name, default)

	def hasValue(self, name):
		return self._values.has_key(name)

	def setValue(self, name, value):
		self._values[name] = value

	def values(self):
		return self._values


	## Transactions ##

	def awake(self, trans):
		''' Invoked during the beginning of a transaction, giving a Session an opportunity to perform any required setup. The default implementation updates the 'lastAccessTime'. '''
		self._lastAccessTime = time()
		self._numTrans = self._numTrans + 1

	def respond(self, trans):
		''' The default implementation does nothing, but could do something in the future. Subclasses should invoke super. '''
		pass

	def sleep(self, trans):
		''' Invoked during the ending of a transaction, giving a Session an opportunity to perform any required shutdown. The default implementation does nothing, but could do something in the future. Subclasses should invoke super. '''
		pass

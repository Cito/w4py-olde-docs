from MiscUtils import NoDefault
import time, whrandom


class User:
	'''
	@@ 2001-02-19 ce: docs
	'''


	## Init ##

	def __init__(self, manager, name, password):
		self._creationTime = time.time()
		self._manager = manager
		self.setName(name)
		self.setPassword(password)
		self._isActive = 0
		self._externalId = None


	## Attributes ##

	def manager(self):
		return self._manager

	def serialNum(self):
		return self._serialNum

	def externalId(self):
		if self._externalId is None:
			from time import localtime, time
			prefix = ''.join(map(lambda x: '%02d' % x, localtime(time())[:6]))
			attempts = 0
			while attempts<10000:
				self._externalId = prefix + str(whrandom.randint(10000, 99999))
				# @@ 2001-02-17 ce: check that manager doesn't already have this
				# if mgr.userForExternalId(self._externalId, None) is None:
				#	break
				break
				attempts += 1
			else:
				raise Exception, "Can't create valid external id after %i attempts." % attempts
		return self._externalId

	def name(self):
		return self._name

	def setName(self, name):
		self._name = name
		# @@ 2001-02-15 ce: do we need to notify the manager which may have us keyed by name?

	def password(self):
		return self._password

	def setPassword(self, password):
		self._password = password
		# @@ 2001-02-15 ce: should we make some attempt to cryptify the password so it's not real obvious when inspecting memory?

	def isActive(self):
		return self._isActive

	def creationTime(self):
		return self._creationTime

	def lastAccessTime(self):
		return self._lastAccessTime

	def lastLoginTime(self):
		return self._lastLoginTime


	## Log in and out ##

	def login(self, password, fromMgr=0):
		''' Returns self if the login is successful and None otherwise. '''
		if not fromMgr:
			# Our manager needs to know about this
			# So make sure we go through him
			self.manager().login(self, password)
		else:
			if password==self.password():
				self._isActive = 1
				self._lastLoginTime = self._lastAccessTime = time.time()
				return self
			else:
				if self._isActive:
					# Woops. We were already logged in, but we tried again
					# and this time it failed. Logout:
					self.logout()
				return None

	def logout(self, fromMgr=0):
		if not fromMgr:
			# Our manager needs to know about this
			# So make sure we go through him
			self.manager().logout(self)
		else:
			self._isActive = 0
			self._lastLogoutTime = time.time()


	## Notifications ##

	def wasAccessed(self):
		self._lastAccessTime = time.time()

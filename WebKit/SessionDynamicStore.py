from SessionStore import SessionStore
import SessionMemoryStore, SessionFileStore
import os, time

debug = 0

class SessionDynamicStore(SessionStore):
	"""
	Stores the session in Memory and Files.

	This can be used either in a persistent app server or a cgi framework.

	To use this Session Store, set SessionStore in Application.config to 'Dynamic'.
	Other variables which can be set in Application.config are:
	
	'MaxDynamicMemorySessions', which sets the maximum number of sessions that can be
	in the Memory SessionStore at one time. Default is 10,000.
	
	'DynamicSessionTimeout', which sets the default time for a session to stay in memory
	with no activity.  Default is 15 minutes. When specifying this in Application.config, use minutes.
	
	
	"""


	## Init ##

	def __init__(self, app):
		SessionStore.__init__(self, app)
		self._fileStore = SessionFileStore.SessionFileStore(app)
		self._memoryStore = SessionMemoryStore.SessionMemoryStore(app)
		self._memoryStore.clear()  #fileStore will have the files on disk

		#moveToFileInterval specifies after what period of time a session is automatically moved to file
		self.moveToFileInterval = self.application().setting('DynamicSessionTimeout', 15) * 60

		#minMemoryInterval is the minimum amount of time Sessions will stay in memory
		self.minMemoryInterval = 300 #5 minutes

		#maxMemoryInterval is the maximum amount of time Sessions will stay in memory
		self.maxMemoryInterval = self.moveToFileInterval * 48 #12 hours by default

		#maxDynamicMemorySessions is what the user actually sets in Application.config
		self._maxDynamicMemorySessions = self.application().setting('MaxDynamicMemorySessions', 10000)

		self._fileSweepCount = 0

		if debug:
			print "SessionDynamicStore Initialized"
		
	## Access ##

	def __len__(self):
		return len(self._memoryStore) + len(self._fileStore)

	def __getitem__(self, key):
		if self._fileStore.has_key(key):
			self.MovetoMemory(key)
		#let it raise a KeyError otherwise
		return self._memoryStore[key]
	

	def __setitem__(self, key, item):
		self._memoryStore[key] = item
		try:
			del self._fileStore[key]
		except KeyError:
			pass

	def __delitem__(self, key):
		if self._memoryStore.has_key(key):
			del self._memoryStore[key]
		if self._fileStore.has_key(key):
			del self._fileStore[key]

	def has_key(self, key):
		return self._memoryStore.has_key(key) or self._fileStore.has_key(key)

	def keys(self):
		return self._memoryStore.keys() + self._fileStore.keys()

	def clear(self):
		self._memoryStore.clear()
		self._fileStore.clear()

	def MovetoMemory(self, key):
		global debug
		if debug: print ">> Moving %s to Memory" % key
		self._memoryStore[key] = self._fileStore[key]
		del self._fileStore[key]

	def MovetoFile(self, key):
		global debug
		if debug: print ">> Moving %s to File" % key
		self._fileStore[key] = self._memoryStore[key]
		del self._memoryStore[key]
		


	## Application support ##

	def storeSession(self, session):
		pass

	def storeAllSessions(self):
		for i in self._memoryStore.keys():
			self.MovetoFile(i)

	def cleanStaleSessions(self, task=None):
		"""
		Called by the Application to tell this store to clean out all sessions that have
		exceeded their lifetime.
		We want to have their native class functions handle it, though.

		Ideally, intervalSweep would be run more often than the cleanStaleSessions functions
		for the actual stores.  This may need to wait until we get the TaskKit in place, though.
		
		The problem is the FileStore.cleanStaleSessions can take a while to run.
		So here, we only run the file sweep every fourth time.
		"""
		if debug: print "Session Sweep started"
		try:
			if self._fileSweepCount == 0:
				self._fileStore.cleanStaleSessions(task)
			self._memoryStore.cleanStaleSessions(task)
		except KeyError:
			pass
		if self._fileSweepCount < 4:
			self._fileSweepCount = self._fileSweepCount + 1
		else:
			self._fileSweepCount = 0
		#now move sessions from memory to file as necessary
		self.intervalSweep()

		
#It's OK for a session to moved from memory to file or vice versa in between the time we get the keys and the time we actually ask for the session's access time.  It may take a while for the fileStore sweep to get completed.  


	def intervalSweep(self):
		"""
		The interval function moves sessions from memory to file. and can be run more often than the full
		cleanStaleSessions function.
		
		"""
		global debug
		if debug:
			print "Starting interval Sweep at %s" % time.ctime(time.time())
			print "Memory Sessions: %s   FileSessions: %s" % (len(self._memoryStore), len(self._fileStore))
			print "maxDynamicMemorySessions = %s" % self._maxDynamicMemorySessions
			print "moveToFileInterval = %s" % self.moveToFileInterval
			
		now = time.time()
		
		delta = now - self.moveToFileInterval
		for i in self._memoryStore.keys():
			if self._memoryStore[i].lastAccessTime() < delta:
				self.MovetoFile(i)

		#If we didn't get enough, find a tighter interval for next time
		if len(self._memoryStore) > self._maxDynamicMemorySessions \
		   and self.moveToFileInterval > self.minMemoryInterval:
			self.moveToFileInterval = self.findInterval()
			
		#IF we have excess capacity in memory, increase the interval
		elif len(self._memoryStore) < (.5 * self._maxDynamicMemorySessions)\
			 and self.moveToFileInterval < self.maxMemoryInterval:
			self.moveToFileInterval = self.moveToFileInterval * 2

			
		if debug: print "Finished interval Sweep at %s" % time.ctime(time.time())
		if debug: print "Memory Sessions: %s   FileSessions: %s" % (len(self._memoryStore), len(self._fileStore))

		
	def findInterval(self):
		"""
		Intelligently (?) find a period of time that will get the memory store down to it's maximum level
		"""
		global debug
		if debug: print "Finding Interval"
		
		keys = self._memoryStore.keys()
		keys.sort(self.sortFunc)
		count = 0
		while count < self._maxDynamicMemorySessions:
			count = count+1
		newinterval =  time.time() - self._memoryStore[keys[count]].lastAccessTime()

		if debug: print "Found new interval: %s" % newinterval
		if newinterval > self.minMemoryInterval:
			return newinterval #5 minutes is minimum
		else:
			return self.minMemoryInterval

	def sortFunc(self,x,y):
		if self._memoryStore[x].lastAccessTime() > self._memoryStore[y].lastAccessTime():
			return -1
		else:
			return 1
		
			

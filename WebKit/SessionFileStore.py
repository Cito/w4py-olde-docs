from SessionStore import SessionStore
import os
from glob import glob

debug = 0


class SessionFileStore(SessionStore):
	'''
	Stores the sessions on disk in the Sessions/ directory, one file
	per session.

	This is useful for various situations:
		1. Using the OneShot adapter
		2. Doing development (so that restarting the app server won't
		   lose session information).
		3. Fault tolerance
		4. Clustering

	Note that the last two are not yet supported by WebKit (as of 0.4,
	8/2000).
	'''


	## Init ##

	def __init__(self, app):
		SessionStore.__init__(self, app)
		self._sessionDir = app.serverSidePath('Sessions')


	## Access ##

	def __len__(self):
		if debug:
			print '>> len', len(self.keys())
		return len(self.keys())

	def __getitem__(self, key):
		if debug:
			print '>> get (%s)' % key
		filename = self.filenameForKey(key)
		try:
			file = open(filename)
		except IOError:
			raise KeyError, key
		item = self.decoder()(file)
		file.close()
		return item

	def __setitem__(self, key, item):
		if debug:
			print '>> setitem(%s,%s)' % (key, item)
		filename = self.filenameForKey(key)
		file = open(filename, 'w')
		self.encoder()(item, file)

	def __delitem__(self, key):
		filename = self.filenameForKey(key)
		if not os.path.exists(filename):
			raise KeyError, key
		os.remove(filename)

	def has_key(self, key):
		return os.path.exists(self.filenameForKey(key))

	def keys(self):
		start = len(self._sessionDir)+1
		end = -len('.ses')
		keys = glob(os.path.join(self._sessionDir, '*.ses'))
		keys = map(lambda key, start=start, end=end: key[start:end], keys)
		if debug:
			print '>> keys =', keys
		return keys

	def clear(self):
		for filename in glob(os.path.join(self._sessionDir,'*.ses')):
			os.remove(filename)


	## Application support ##

	def storeSession(self, session):
		key = session.identifier()
		self[key] = session

	def storeAllSessions(self):
		pass

##	def cleanStaleSessions(self, task=None):
##		"""
##		Called by the Application to tell this store to clean out all sessions that
##		have exceeded their lifetime.
##		"""
##	    we don't know the timeout without opening the session, so his can't work.
##		curTime = time.time()
##		for key in self.keys():
##			mtime = os.path.getmtime(self.filenameForKey(key))
##			if (curTime - mtime) >= sess.timeout()  or  sess.timeout()==0:
##				sess.expiring()
##				del self[key]

	## Self utility ##

	def filenameForKey(self, key):
		return self._sessionDir + '/%s.ses' % key

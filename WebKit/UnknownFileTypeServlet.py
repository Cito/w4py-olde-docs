from ServletFactory import ServletFactory
import os, mimetypes, time

debug = 0

class UnknownFileTypeServletFactory(ServletFactory):
	"""
	This is the factory for files of an unknown type (e.g., not .py .psp, etc).
	"""

	def uniqueness(self):
		return 'file'

	def extensions(self):
		return ['.*']

	def servletForTransaction(self, transaction):
		return UnknownFileTypeServlet(transaction.application())

	def flushCache(self):
		pass


from HTTPServlet import HTTPServlet
from MiscUtils.Configurable import Configurable
class UnknownFileTypeServlet(HTTPServlet, Configurable):

	def __init__(self, application):
		HTTPServlet.__init__(self)
		Configurable.__init__(self)
		self._application = application
		self._content = None
		self._serverSideFilename = None
		self._mimeType = None
		self._mimeEncoding = None

	def userConfig(self):
		""" Get the user config from the 'UnknownFileTypes' section in the Application's configuration. """
		return self._application.setting('UnknownFileTypes')

	def canBeReused(self):
		return self.setting('ReuseServlets')

	def validTechniques(self):
		return ['serveContent', 'redirectSansAdapter']

	def respondToGet(self, trans):
		""" Responds to the transaction by invoking self.foo() for foo is specified by the 'Technique' setting. """
		technique = self.setting('Technique')
		assert technique in self.validTechniques(), 'technique = %s' % technique
		method = getattr(self, technique)
		method(trans)

	respondToHead = respondToGet

	def respondToPost(self, trans):
		"""
		Invokes self.respondToGet().
		Since posts are usually accompanied by data, this might not be the best policy. However, a POST would most likely be for a CGI, which currently no one is mixing in with their WebKit-based web sites.
		"""
		# @@ 2001-01-25 ce: See doc string for why this might be a bad idea.
		self.respondToGet(trans)

	def redirectSansAdapter(self, trans):
		""" Sends a redirect to a URL that doesn't contain the adapter name. Under the right configuration, this will cause the web server to then be responsible for the URL rather than the app server. This has only been test with "*.[f]cgi" adapters.
		Keep in mind that links off the target page will NOT include the adapter in the URL. """
		# @@ 2000-05-08 ce: the following is horribly CGI specific and hacky
		env = trans.request()._environ
		# @@ 2001-01-25 ce: isn't there a func in WebUtils to get script name? because some servers are different?
		newURL = os.path.split(env['SCRIPT_NAME'])[0] + env['PATH_INFO']
		import string
		newURL = string.replace(newURL, '//', '/')  # hacky
		trans.response().sendRedirect(newURL)


	def serveContent(self, trans):

		response = trans.response()

		# @@temp variable, move to config
		MaxCacheContentSize = 1024*32 ##32k

		#start sending automatically
		response.streamOut().autoCommit(1)

		filename = trans.request().serverSidePath()
		filesize = os.path.getsize(filename)

		isHead = trans.request().method().upper()[0]=='H' # as in HEAD
		if isHead:
			response.setHeader('Content-Length', str(filesize))
			mtime = os.path.getmtime(filename)
			response.setHeader('Last-Modified',
				time.strftime('%a, %d %b %Y %H:%M:%S GMT',
				time.gmtime(mtime)))

		if debug:
			print '>> UnknownFileType.serveContent()'
			print '>> filename =', filename
		if self._content != None:
			# We already have content in memory:
			assert self._serverSideFilename==filename
			if self.setting('CheckDate'):
				# check the date and re-read if necessary
				actual_mtime = os.path.getmtime(filename)
				if actual_mtime>self._mtime:
					if debug: print '>> reading updated file'
					self._content = open(filename, 'rb').read()
					self._mtime = actual_mtime
			data = self._content
			response.setHeader('Content-type', self._mimeType)
			if self._mimeEncoding:
				response.setHeader('Content-encoding', self._mimeEncoding)
			if isHead:
				return
			response.write(data)

		else:
			if debug: print '>> reading file'
			filetype = mimetypes.guess_type(filename)
			mimeType = filetype[0]
			mimeEncoding = filetype[1]

			if mimeType==None:
				mimeType = 'text/html'  # @@ 2000-01-27 ce: should this just be text?
			response.setHeader('Content-type', mimeType)
			if self._mimeEncoding:
				response.setHeader('Content-encoding', self._mimeEncoding)


			if self.setting('ReuseServlets') and self.setting('CacheContent') and filesize < MaxCacheContentSize:
				# set the:
				#   content, mimeType, mtime and serverSideFilename
				if debug: print '>> caching'
				self._content = open(filename,"rb").read()
				self._mimeType = mimeType
				self._mimeEncoding = mimeEncoding
				self._mtime = os.path.getmtime(filename)
				self._serverSideFilename = filename
				if isHead:
					return
				response.write(self._content)
			else:  ##too big
				if isHead:
					return
				f = open(filename, "rb")
				sent = 0
				while sent < filesize:
					data = f.read(8192)
					response.write(data)
					sent = sent + len(data)

from ServletFactory import ServletFactory
import os, mimetypes

class UnknownFileTypeServletFactory(ServletFactory):
	"""
	This is the factory for files of an unknown type (e.g., not .py, not .psp, etc.).

	The servlet returned will simply redirect the client to a URL that does not include
	the adaptor's filename.
	"""

	def __init__(self,app):
		ServletFactory.__init__(self,app)
		self._servlet = UnknownFileTypeServlet()

	def uniqueness(self):
		return 'file' # should really be 'application', but that's not supported yet.

	def extensions(self):
		return ['.*']

	def servletForTransaction(self, transaction):
		return self._servlet


from HTTPServlet import HTTPServlet
class UnknownFileTypeServlet(HTTPServlet):

	def canBeReused(self):
		"""don't want a bunch of references to this building up"""
		return 0

       	def respondToGet(self, trans):
		fnm=trans.request().serverSidePath()
		data=open(fnm,'rb').read()

		trans.response().write(data)

		fnm=os.path.split(fnm)[1]
		content=mimetypes.guess_type(fnm)[0]
		if content == None: content = 'text/html'

		trans.response().setHeader('Content-type',content)


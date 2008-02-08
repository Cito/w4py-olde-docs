from os.path import exists, splitext

from AdminSecurity import AdminSecurity


class View(AdminSecurity):
	"""View a text or html file.

	The Admin View servlet loads any text or html file
	in your application working directory on the Webware server
	and displays it in the browser for your viewing pleasure.

	"""

	def defaultAction(self):
		self.data = self.type = None
		self.writeHTML()
		if self.data and self.type:
			try:
				response = self.response()
				response.reset()
				response.setHeader('Content-type', self.type)
				self.write(self.data)
			except Exception:
				self.writeError('File cannot be viewed!')

	def writeError(self, message):
		self.writeln('<h3 style="color:red">Error</h3>'
			'<p>%s</p>' % message)

	def writeContent(self):
		fn = self.request().field('filename', None)
		if not fn:
			self.writeError('No filename given to view!')
			return
		fn = self.application().serverSidePath(fn)
		if not exists(fn):
			self.writeError('The requested file %r does not exist'
				' in the server side directory.' % fn)
			return
		self.type = 'text/%s' % (splitext(fn)[1] in ('.htm', '.html')
			and 'html' or 'plain')
		try:
			self.data = open(fn).read()
		except Exception:
			self.writeError('The requested file %r cannot be read.' % fn)

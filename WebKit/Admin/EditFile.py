from WebKit.Page import Page


class EditFile(Page):
	"""Helper servlet for the feature provided by the IncludeEditLink setting."""

	def writeInfo(self, key, value):
		self.writeln('%s: %s' % (key, value))

	def writeHTML(self):
		header = self.response().setHeader
		info = self.writeInfo
		field = self.request().field
		app = self.application()

		header('Content-type', 'application/x-webkit-edit-file')
		header('Content-Disposition', 'inline; filename="WebKit.EditFile"')

		# Basic information for editing the file:
		info('Filename', field('filename'))
		info('Line', field('line'))

		# Additional information about this Webware installation:
		info('ServerSidePath', app.serverSidePath())
		info('WebwarePath', app.webwarePath())
		info('WebKitPath', app.webKitPath())

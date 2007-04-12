from ExamplePage import ExamplePage


class RequestInformation(ExamplePage):
	"""Request information demo."""

	def writeContent(self):
		self.writeln('<h3>Request Variables</h3>')
		self.writeln('<p>The following table shows the values for various request variables.</p>')
		self.writeln('<table style="background-color:#EEEEFF;width:100%"'
			' border="0" cellpadding="2" cellspacing="4" width="100%">')
		self.dict('HTTPRequest.fields()', self.request().fields())
		self.dict('HTTPRequest._environ', self.request()._environ)
		self.dict('Cookies', self.request().cookies())
		self.writeln('</table>')
		self.response().setCookie('TestCookieName','CookieValue')
		self.response().setCookie('TestExpire1','Expires in 1 minutes', expires='+1m')

	def pair(self, key, value):
		valueType = type(value)
		if valueType is type([]) or valueType is type(()):
			value = ', '.join(map(str, value))
		self.writeln('<tr valign="top"><td>%s</td><td>%s</td></tr>'
			% (key, self.htmlEncode(str(value))))

	def list(self, codeString):
		list = eval(codeString)
		assert type(list) is type([])  or  type(list) is type(())
		self.pair(codeString, list)

	def dict(self, name, dict):
		self.writeln('<tr valign="top">'
			'<td style="background-color:#CCCCFF" colspan="2">%s</td>'
			'</tr>' % (name))
		keys = dict.keys()
		keys.sort()
		for name in keys:
			self.writeln('<tr valign="top"><td>%s</td><td>%s</td></tr>' % (name,
				self.htmlEncode(str(dict[name])).replace(
					'\n', '<br>').replace(',', ', ').replace(';', '; ')))

from ExamplePage import ExamplePage

class Welcome(ExamplePage):

	def writeBody(self):
		server = self.application().server()
		if server is None:
			version = ''
		else:
			version = ' %s' % server.version()
		self.writeln('<p> Welcome to WebKit%s!' % version)
		self.writeln('''<p> Along the top of this page you will find links to other example servlets/pages written with WebKit.
<p> At the bottom of the page you will see a <b>source</b> link that will display for you the source code of the current example.
<p> You will also see an <b>admin</b> link which will take you to the main administration page for the app server.
''')

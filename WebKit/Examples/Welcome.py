from ExamplePage import ExamplePage

class Welcome(ExamplePage):

	def writeContent(self):
		self.writeln('<p> Welcome to WebKit %s!' % self.application().webKitVersion())
		self.writeln('''<p> Along the side of this page you will see various links that will take you to:

		<ul>
			<li> The different WebKit examples.
			<li> The source code of the current example.
			<li> The local WebKit documentation.
			<li> Whatever contexts have been configured. Each context represents a distinct set of web pages, usually given a descriptive name.
			<li> External sites, such as the Webware home page.
		</ul>

		<p> The <b>Admin</b> context is particularly interesting because it takes you to the administrative pages for the WebKit AppServer where you can review logs, configuration, plug-ins, etc.
''')

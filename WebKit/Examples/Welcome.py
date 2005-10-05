from ExamplePage import ExamplePage

class Welcome(ExamplePage):

	def writeContent(self):
		self.writeln('<h2>Welcome to WebKit %s!</h2>' % self.application().webKitVersionString())
		adapter = self.request().adapterName()
		self.writeln('''\
		<p> Along the side of this page you will see various links that will take you to:</p>
		<ul>
			<li>The different WebKit examples.</li>
			<li>The source code of the current example.</li>
			<li>Whatever contexts have been configured.
				Each context represents a distinct set of web pages,
				usually given a descriptive name.</li>
			<li>External sites, such as the Webware home page.</li>
		</ul>
		<p>The <a href="%(adapter)s/Admin/">Admin</a> context is particularly interesting because
		it takes you to the administrative pages for the WebKit application server where
		you can review logs, configuration, plug-ins, etc.</p>
		<p>The <a href="%(adapter)s/Docs/">Docs</a> contexts allow you to browse
		the documentation of <a href="%(adapter)s/WebKit/Docs/">WebKit</a>
		and <a href="%(adapter)s/Docs/ComponentIndex.html">all other components</a>
		of <a href="%(adapter)s/Docs/">Webware for Python</a>.</p>''' % locals())
		from os.path import join
		self.writeln('<p>The location of the WebKit documentation on the server is:</p>')
		self.writeln('<blockquote>%s</blockquote>' % join(self.application().webKitPath(), 'Docs'))
		self.writeln('<p>The documentation for Webware for Python is located here:</p>')
		self.writeln('<blockquote>%s</blockquote>' % join(self.application().webwarePath(), 'Docs'))
		req = self.request()
		extraURLPath = req.extraURLPath()
		if extraURLPath and extraURLPath != '/':
			self.writeln('''
			<p>extraURLPath information was found on the URL,
			and a servlet was not found to process it.
			Processing has been delegated to this servlet.</p>''')
			self.writeln('<ul>')
			self.writeln('<li>serverSidePath of this servlet is: <tt>%s</tt></li>' % req.serverSidePath())
			self.writeln('<li>extraURLPath data is: <tt>%s</tt></li>' % extraURLPath)
			self.writeln('</ul>')



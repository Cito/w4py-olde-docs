from Page import Page


class SidebarPage(Page):
	"""WebKit page template class for pages with a sidebar.

	SidebarPage is an abstract superclass for pages that have a sidebar
	(as well as a header and "content well"). Sidebars are normally used
	for navigation (e.g., a menu or list of links), showing small bits
	of info and occasionally a simple form (such as login or search).

	Subclasses should override cornerTitle(), writeSidebar() and
	writeContent() (and title() if necessary; see Page).

	The utility methods menuHeading() and menuItem() can be used by
	subclasses, typically in their implementation of writeSidebar().

	WebKit itself uses this class: Examples/ExamplePage and Admin/AdminPage
	both inherit from it.

	TO DO
	* More consequent use style sheets; get rid of tables completely.
	* The header, corner and colors are not easy to customize via subclasses.

	"""


	## StyleSheet ##

	def writeStyleSheet(self):
		"""We're using a simple internal style sheet.

		This way we avoid having to care about where an external style
		sheet should be located when this class is used in another context.

		"""
		self.writeln('''<style type="text/css">
<!--
body {
	color: #080810;
	background-color: white;
	font-size: 11pt;
	font-family: Tahoma,Verdana,Arial,Helvetica,sans-serif;
	margin: 0pt;
	padding: 0pt;
}
h1 { font-size: 18pt; }
h2 { font-size: 16pt; }
h3 { font-size: 14pt; }
h4 { font-size: 12pt; }
h5 { font-size: 11pt; }
-->
</style>''')


	## Content methods ##

	def writeBodyParts(self):

		# begin
		wr = self.writeln
		wr('<table border="0" cellpadding="0" cellspacing="0" width="100%">')

		# banner
		self.writeBanner()

		# sidebar
		wr('<tr><td style="background-color:#E8E8F0;'
			'padding:4pt;font-size:10pt;'
			'vertical-align:top;white-space:nowrap;height:100%">')
		self.writeSidebar()
		wr('</td>')

		# content
		wr('<td style="padding:8pt;vertical-align:top;width:100%">')
		self.writeContent()
		wr('</td>')

		# end
		wr('</tr></table>')

	def writeBanner(self):
		# header
		title, cornerTitle = self.title(), self.cornerTitle()
		self.writeln('<tr><td style="background-color:#101040;color:white;'
			'padding:6pt 6pt;font-size:14pt;'
			'text-align:center;vertical-align:middle">'
			'%s</td><td style="background-color:#202080;color:white;'
			'padding:8pt 6pt;font-size:16pt;font-weight:bold;'
			'text-align:center;vertical-align:middle">'
			'%s</td></tr>' % (cornerTitle, title))

	def writeSidebar(self):
		self.writeWebKitSidebarSections()

	def cornerTitle(self):
		return ''


	## Menu ##

	def menuHeading(self, title):
		self.writeln('<div style="font-weight:bold;'
			'margin-top:6pt;margin-bottom:3pt;width:12em">%s</div>' % title)
		self._wroteHeading = 1

	def menuItem(self, title, url=None, suffix=None, indentLevel=1):
		if suffix:
			suffix = ' ' + suffix
		else:
			suffix = ''
		if url is not None:
			title = '<a href="%s">%s</a>' % (url, title)
		self.writeln('<div style="margin-left:%dpt">%s%s</div>'
			% (4*indentLevel, title, suffix))


	## WebKit sidebar sections ##

	def writeWebKitSidebarSections(self):
		"""Write sidebar sections.

		This method (and consequently the methods it invokes)
		are provided for WebKit's example and admin pages.
		It writes sections such as contexts, e-mails, exits and versions.

		"""
		self.writeContextsMenu()
		self.writeWebwareEmailMenu()
		self.writeWebwareExitsMenu()
		self.writeVersions()

	def writeContextsMenu(self):
		self.menuHeading('Contexts')
		adapterName = self.request().adapterName()
		ctxs = self.application().contexts().keys()
		ctxs = filter(lambda ctx: ctx!='default' and ctx.find('/')<0, ctxs)
		ctxs.sort()
		for ctx in ctxs:
			self.menuItem(ctx, '%s/%s/' % (adapterName, ctx))

	def writeWebwareEmailMenu(self):
		self.menuHeading('E-mail')
		self.menuItem('webware-discuss', 'mailto:webware-discuss@lists.sourceforge.net')

	def writeWebwareExitsMenu(self):
		self.menuHeading('Exits')
		self.menuItem('Webware', 'http://www.webwareforpython.org')
		self.menuItem('Python', 'http://www.python.org')

	def writeVersions(self):
		app = self.application()
		self.menuHeading('Versions')
		self.menuItem('WebKit ' + app.webKitVersionString())
		self.menuItem('Webware ' + app.webwareVersionString())
		import string, sys
		self.menuItem('Python ' + string.split(sys.version)[0])

	def writeContent(self):
		self.writeln('Woops, someone forgot to override writeContent().')

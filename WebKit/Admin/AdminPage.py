from Page import Page
import os


class AdminPage(Page):
	'''
	AdminPage is the abstract superclass of all WebKit administration
	pages.

	Subclasses typically override title() and writeContent(), but may
	customize other methods.

	This class defines the sidebar that is seen on all pages for
	navigation purposes.
	'''

	## Content methods ##

	def writeHeader(self):
		self.writeln('''
			<head>
				<title>%s</title>
			</head>
			<body %s>''' % (
			self.title(), self.htBodyArgs()))

	def writeBody(self):
		# begin
		wr = self.writeln
		wr('<table border=0 cellpadding=0 cellspacing=0 width=100%>')

		# banner
		self.writeBanner()

		# sidebar
		wr('<tr> <td bgcolor=EEEEEF valign=top>')
		self.writeSidebar()
		wr('</td>')

		# spacer
		wr('<td> &nbsp;&nbsp;&nbsp; </td>')

		# content
		wr('<td valign=top width=90%><p><br>')
		self.writeContent()
		wr('</td>')

		# end
		wr('</tr> </table>')

	def writeBanner(self):
		# header
		title = self.title()
		startFont1 = '<font face="Tahoma, Arial, Helvetica, sans-serif" color=white size=+1>'
		endFont1 = '</font>'
		startFont2 = '<font face="Tahoma, Arial, Helvetica, sans-serif" color=white size=+2><b>'
		endFont2 = '</b></font>'
		self.writeln('''
			<tr>
				<td align=center bgcolor=000000>%(startFont1)sWebKit AppServer%(endFont1)s</td>
				<td align=center bgcolor=00008B colspan=2>&nbsp;<br>%(startFont2)s%(title)s%(endFont2)s<br>&nbsp;</td>
			</tr>''' % locals())

	def writeSidebar(self):
		app = self.application()
		self.startMenu()

		self.menuHeading('Admin')
		self.menuItem('Home', '')
		self.menuItem('Activity log', 'Access', self.fileSize('ActivityLogFilename'))
		self.menuItem('Error log', 'Errors', self.fileSize('ErrorLogFilename'))
		self.menuItem('Config', 'Config')
		self.menuItem('Plug-ins', 'PlugIns')
		self.menuItem('Servlet cache by path', 'ServletCacheByPath')

		self.menuHeading('Contexts')
		adapterName = self.request().adapterName()
		ctxs = self.application().contexts().keys()
		ctxs = filter(lambda ctx: ctx!='default', ctxs)
		ctxs.sort()
		for ctx in ctxs:
			self.menuItem(ctx, '%s/%s/' % (adapterName, ctx))

		self.menuHeading('E-mail')
		self.menuItem('webware-discuss', 'mailto:webware-discuss@lists.sourceforge.net')

		self.menuHeading('Exits')
		self.menuItem('Webware', 'http://webware.sourceforge.net')
		self.menuItem('Python', 'http://www.python.org')

		# To ensure a minimum width of the sidebar
		# Technique learned from www.python.org
		self.writeln('<img width=175 height=1 src=MenuBar.gif>')

		self.endMenu()

	def writeContent(self):
		self.writeln('Woops. Forget to override writeContent().')

	def writeFooter(self):
		app = self.application()

		self.writeln('''
			<p><hr>
				<center>
					<font face="Arial, Helvetica" size=-1>
						WebKit %s, part of Webware %s
					</font>
				</center>
			</body>
		''' % (app.webKitVersion(), app.webwareVersion()))


	## Menu ##

	def startMenu(self):
		self.writeln('<table border=0 cellpadding=0 cellspacing=4><tr><td><font face=Arial size=-1>')
		self._wroteHeading = 0

	def menuHeading(self, title):
		if self._wroteHeading:
			self.write('<br>')
		self.writeln('<b>%s</b><br>' % title)
		self._wroteHeading = 1

	def menuItem(self, title, url, extra=None):
		if extra:
			extra = extra + ' '
		else:
			extra = ''
		self.writeln(' &nbsp; <a href="%s">%s</a> %s<br>' % (url, title, extra))

	def endMenu(self):
		self.writeln('</font></td></tr></table>')

	def fileSize(self, filename):
		''' Utility method for writeMenu() to get the size of a configuration file. Returns an HTML string. '''
		filename = self.application().setting(filename)
		if os.path.exists(filename):
			return '<font size=-1>(%0.0f KB)</font>' % (os.path.getsize(filename)/1024.0)
		else:
			return '<font size=-1>(does not exist)</font>'

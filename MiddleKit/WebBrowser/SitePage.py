from WebKit.Page import Page
from MiscUtils.Configurable import Configurable
import os


class SitePage(Page, Configurable):

	def __init__(self):
		Page.__init__(self)
		Configurable.__init__(self)

	def configFilename(self):
		return self.request().relativePath('Properties.config')

	def printDict(self, dict):
		for key, value in dict.items():
			print '  %s = %s' % (key, value)

	def writeHTML(self):
		if 1:
			req = self.request()
			print '>> About to writeHTML()'
			print '>> fields:'
			self.printDict(req.fields())
			print '>> cookies:'
			self.printDict(req.cookies())
			print
		Page.writeHTML(self)

	def writeHeader(self):
		self.writeln('''\
<head>
	<title>%s</title>
	<link rel=stylesheet href=StyleSheet.css type=text/css>
</head>
<body>''' % self.title())

	def writeBody(self):
		wr = self.writeln
		wr('<table border=0 cellpadding=2 cellspacing=0 width=100%>')

		wr('<tr> <td colspan=2 class=TitleBar>')
		self.writeTitleBar()
		wr('</td> </tr>')

		wr('<tr> <td colspan=2 class=TopBar>')
		self.writeTopBar()
		wr('</td> </tr>')

		wr('<tr>')
		wr('<td valign=top width=5% class=SideBar>')
		self.writeSideBar()
		wr('</td>')

		wr('<td valign=top width=95% class=ContentWell>')
		self.writeContent()
		wr('</td>')
		wr('</tr>')

		wr('</table>')

	def writeTitleBar(self):
		self.writeln('MiddleKit Browser')

	def writeTopBar(self):
		self.writeln('&nbsp;')

	def writeSideBar(self):
		pass

	def writeHeading(self, heading):
		self.writeln('<p><span class=Heading>%s</span>' % heading)

	def writeHelp(self):
		self.writeHeading('Help')
		self.writeln(self.help())

	def help(self, name=None):
		''' Returns the body text for help on this page. Loaded from SelectModelHelp.htmlf. '''
		if not name:
			name = self.__class__.__name__
		filename = self.request().relativePath('Help/%s.htmlf' % name)
		help = open(filename).read()
		help = '<span class=Help>%s</span>' % help
		return help

	def saveFieldsToCookies(self):
		res = self.response()
		for name, value in self.request().fields().items():
			res.setCookie(name, value)

	def hostName(self):
		''' Returns the name of the host, using the external command 'hostname' found on most flavors of UNIX and recent flavors of Windows. We can't rely on os.environ because in a web environment it might not be passed. We can't rely on the CGI standard HTTP_HOST, because it often returns 127.0.0.1, when it's the name that we want. '''
		return os.popen('hostname').read().strip()

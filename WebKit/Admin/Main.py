from time import time, localtime, gmtime, asctime
from AdminPage import AdminPage
from WebUtils.WebFuncs import URLEncode
import os

# @@ 2000-06-02 ce: We should show all the contexts of the application here


class Main(AdminPage):

	def title(self):
		return 'Admin'

	def writeBody(self):
		app = self.application()
		curTime = time()
		self.writeGeneralInfo()
		self.writePlugIns()
		self.writeMenu()
		self.writeSignature()

	## General Info ##

	def writeGeneralInfo(self):
		app = self.application()
		curTime = time()
		info = [
			('Version',      app.webKitVersion()),
			('Global Time',  asctime(gmtime(curTime))),  # @@ 2000-06-02 ce: do we need global time?
			('Local Time',   asctime(localtime(curTime))),
			('Up Since',     asctime(localtime(app.server().startTime()))),
			('Num Requests', app.server().numRequests()),
			('Working Dir',  os.getcwd()),
		]

		self.writeln('<table align=center cellspacing=0 cellpadding=0 border=0>')
		for label, value in info:
			self.writeln('<tr> <td> <b>%s:</b> </td> <td>%s</td> </tr>' % (label, value))
		self.writeln('</table>')


	## Menu ##

	def writeMenu(self):
		app = self.application()
		self.startMenu()
		self.menuItem('Activity log', 'Access', self.fileSize('ActivityLogFilename'))
		self.menuItem('Error log', 'Errors', self.fileSize('ErrorLogFilename'))
		self.menuItem('Show config', 'Config')
		self.menuItem('Servlet cache by path', 'ServletCacheByPath')
		self.endMenu()

	def startMenu(self):
		self.writeln('''<p><table align=center border=0 cellspacing=2 cellpadding=2 bgcolor=#FFFFDD>
<tr bgcolor=black><td align=center><font face="Arial, Helvetica" color=white><b>Menu</b></font></td></tr>''')

	def menuItem(self, title, url, extra=None):
		if extra:
			extra = extra + ' '
		else:
			extra = ''
		self.writeln('<tr><td> <a href="%s">%s</a> %s</td></tr>' % (url, title, extra))

	def endMenu(self):
		self.writeln('</table>')

	def fileSize(self, filename):
		''' Utility method for writeMenu() to get the size of a configuration file. Returns an HTML string. '''
		filename = self.application().setting(filename)
		if os.path.exists(filename):
			return '<font size=-1>(%0.0f KB)</font>' % (os.path.getsize(filename)/1024.0)
		else:
			return '<font size=-1>(does not exist)</font>'


	## Plug-ins ##

	def writePlugIns(self):
		# @@ 2000-06-02 ce: We should allow a custom admin link for each plug-in (if it provides one)
		# @@ 2000-06-02 ce: We should have a link to the plug-in's docs
		plugIns = self.application().server().plugIns()
		if plugIns:
			self.writeln('''<p><table align=center border=0 cellspacing=2 cellpadding=2>
<tr bgcolor=black><td align=center colspan=3><font face="Arial, Helvetica" color=white><b>Plug-ins</b></font></td></tr>''')
			for plugIn in plugIns:
				name, dir, ver = plugIn.name(), plugIn.directory(), plugIn.version()
				self.writeln('<tr> %(td)s %(name)s </td> %(td)s %(ver)s </td> %(td)s %(dir)s </td> </tr>' % {
					'name': name,
					'ver': ver,
					'dir': dir,
					'td': '<td bgcolor=#DDDDDD>'
				})
			self.writeln('</table>')


	## Signature ##

	def writeSignature(self):
		app = self.application()
		curTime = time()
		self.writeln('''
<!--
begin-parse
{
	'Version': %s,
	'LocalTime': %s,
	'GlobalTime': %s
}
end-parse
-->''' % (repr(app.webKitVersion()), repr(localtime(curTime)), repr(gmtime(curTime))))

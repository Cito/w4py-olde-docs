from time import time, localtime, gmtime, asctime
from AdminPage import AdminPage

class _admin(AdminPage):

	def title(self):
		return 'Admin'

	def writeBody(self):
		app = self.application()
		curTime = time()
		self.writeln('''
	<table align=center cellspacing=0 cellpadding=0 borde=0>
		<tr> <td><b>Version:</b></td> <td>%s</td> </tr>
		<tr> <td><b>Local time:</b></td> <td>%s</td> </tr>
		<tr> <td><b>Global time:</b></td> <td>%s</td> </tr>
	</table>
	''' % (app.webKitVersion(), asctime(localtime(curTime)), asctime(gmtime(curTime))))

		self.startMenu()
		# @@ 2000-04-21 ce: use URLEncode() here.
		self.menuItem('Activity log', '_dumpCSV?filename=%s' % app.setting('ActivityLogFilename'))
		self.menuItem('Error log', '_dumpErrors?filename=%s' % app.setting('ErrorLogFilename'))
		self.menuItem('Show config', '_showConfig')
		self.endMenu()
			
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

	def startMenu(self):
		self.writeln('''<p><table align=center border=0 cellspacing=2 cellpadding=2 bgcolor=#FFFFDD>
<tr bgcolor=black><td align=center><font face="Arial, Helvetica" color=white><b>Menu</b></font></td></tr>''')

	def menuItem(self, title, url):
		self.writeln('<tr><td> <a href="%s">%s</a> </td></tr>' % (url, title))
	
	def endMenu(self):
		self.writeln('</table>')

from time import time, localtime, gmtime, asctime
from AdminPage import AdminPage
from WebUtils.WebFuncs import URLEncode
import os

class _admin(AdminPage):

	def title(self):
		return 'Admin'

	def writeBody(self):
		app = self.application()
		curTime = time()
		self.writeln('''
			<table align=center cellspacing=0 cellpadding=0 borde=0>
				<tr> <td><b>Version:</b></td> <td>%(ver)s</td> </tr>
				<tr> <td><b>Global time:</b></td> <td>%(globalTime)s</td> </tr>
				<tr> <td><b>Local time:</b></td> <td>%(localTime)s</td> </tr>
				<tr> <td><b>Up since:</b></td> <td>%(upSince)s</td> </tr>
				<tr> <td><b>Num requests:</b></td> <td>%(numRequests)d</td> </tr>
			</table>
		''' % {
			'ver': app.webKitVersion(),
			'globalTime': asctime(gmtime(curTime)),
			'localTime': asctime(localtime(curTime)),
			'upSince': asctime(localtime(app.server().startTime())),
			'numRequests': app.server().numRequests()
		})

		self.startMenu()
		activityLogURL = '_dumpCSV?filename=%s' % URLEncode(app.setting('ActivityLogFilename'))
		errorLogURL = '_dumpErrors?filename=%s' % URLEncode(app.setting('ErrorLogFilename'))
		self.menuItem('Activity log', activityLogURL, self.fileSize('ActivityLogFilename'))
		self.menuItem('Error log', errorLogURL, self.fileSize('ErrorLogFilename'))
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

	def fileSize(self, filename):
		''' Utility method for writeBody() to get the size of a configuration file. Returns an HTML string. '''
		filename = self.application().setting(filename)
		if os.path.exists(filename):
			return '<font size=-1>(%0.0f KB)</font>' % (os.path.getsize(filename)/1024.0)
		else:
			return '<font size=-1>(does not exist)</font>'

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

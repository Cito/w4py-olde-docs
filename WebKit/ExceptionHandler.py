from Common import *
import string, time, traceback, types, whrandom
from time import asctime, localtime
from WebUtils.HTMLForException import HTMLForException
from WebUtils.Funcs import htmlForDict
from HTTPResponse import HTTPResponse


class ExceptionHandler(Object):
	'''
	ExceptionHandler is a utility class for Application that is created
	to handle a particular exception. The object is a one-shot deal.
	After handling an exception, it should be removed.

	See the WebKit.html documentation for other information.
	'''


	## Init ##

	def __init__(self, application, transaction, excInfo):
		Object.__init__(self)

		# Keep references to the objects
		self._app = application
		self._tra = transaction
		self._exc = excInfo
		if self._tra:
			self._req = self._tra.request()
			self._res = self._tra.response()
		else:
			self._req = self._res = None

		# Make some repairs, if needed. We use the transaction & response to get the error page back out
		# @@ 2000-05-09 ce: Maybe a fresh transaction and response should always be made for that purpose
		if self._res is None:
			self._res = HTTPResponse()
			self._tra.setResponse(self._res)

		# Get to work
		self.work()


	## Utilities ##

	def setting(self, name):
		return self._app.setting(name)

	def servletPathname(self):
		return self._tra.request().pathTranslated()
		# @@ 2000-05-01 ce: What should this be?
		# @@ 2000-06-28 ce: probaby servletURL()

	def basicServletName(self):
		name = self.servletPathname()
		if name is None:
			return 'unknown'
		else:
			return os.path.basename(name)


	## Exception handling ##

	def work(self):
		''' Invoked by __init__ to do the main work. '''

		self._res.recordEndTime()
		self.logExceptionToConsole()
		self._res.reset()
		if self.setting('ShowDebugInfoOnErrors')==1:
			publicErrorPage = self.privateErrorPage()
		else:
			publicErrorPage = self.publicErrorPage()
		self._res.write(publicErrorPage)

		privateErrorPage = None
		if self.setting('SaveErrorMessages'):
			privateErrorPage = self.privateErrorPage()
			filename = self.saveErrorPage(privateErrorPage)
		else:
			filename = ''

		self.logExceptionToDisk(errorMsgFilename=filename)

		if self.setting('EmailErrors'):
			if privateErrorPage is None:
				privateErrorPage = self.privateErrorPage()
			self.emailException(privateErrorPage)

	def logExceptionToConsole(self, stderr=sys.stderr):
		''' Logs the time, servlet name and traceback to the console (typically stderr). This usually results in the information appearing in console/terminal from which AppServer was launched. '''
		stderr.write('[%s] [error] WebKit: Error while executing script %s\n' % (
			asctime(localtime(self._res.endTime())), self.servletPathname()))
		traceback.print_exc(file=stderr)

	def publicErrorPage(self):
		return '''<html>
	<title>Error</title>
	<body fgcolor=black bgcolor=white>
		%s
		<p> %s
	</body>
</html>
''' % (htTitle('Error'), self.setting('UserErrorMessage'))

	def privateErrorPage(self):
		''' Returns an HTML page intended for the developer with useful information such as the traceback. '''
		html = ['''
<html>
	<title>Error</title>
	<body fgcolor=black bgcolor=white>
%s
<p> %s''' % (htTitle('Error'), self.setting('UserErrorMessage'))]

		html.append(self.htmlDebugInfo())

		html.append('</body></html>')
		return string.join(html, '')

	def htmlDebugInfo(self):
		''' Return HTML-formatted debugging information about the current exception. '''
		html = ['''
%s
<p> <i>%s</i>
''' % (htTitle('Traceback'), self.servletPathname())]

		html.append(HTMLForException(self._exc))

		html.extend([
			htTitle('Misc Info'),
			htmlForDict({
				'time':          asctime(localtime(self._res.endTime())),
				'filename':      self.servletPathname(),
				'os.getcwd()':   os.getcwd(),
				'sys.path':      sys.path
			}),
			htTitle('Fields'),        htmlForDict(self._req.fields()),
			htTitle('Headers'),       htmlForDict(self._res.headers()),
			htTitle('Environment'),   htmlForDict(self._req.environ(), {'PATH': ';'}),
			htTitle('Ids'),           htTable(osIdTable(), ['name', 'value'])])
			# @@ 2000-05-01 ce: Shouldn't we be asking each of the objects (transaction, request, response, ...) for it's debugging info to append? That would be more OOPish.

		if self.setting('IncludeFancyTraceback'):
			html.append(htTitle('Fancy Traceback'))
			try:
				from WebUtils.ExpansiveHTMLForException import ExpansiveHTMLForException
				html.append(ExpansiveHTMLForException(context=self.setting('FancyTracebackContext')))
			except:
				html.append('Unable to generate a fancy traceback.  Make sure that cgitb.py is installed and works properly.  It can be downloaded from <a href="http://web.lfw.org/python/">here</a>.')
				
		return string.join(html, '')

	def saveErrorPage(self, html):
		''' Saves the given HTML error page for later viewing by the developer, and returns the filename used. '''
		filename = self._app.serverSidePath(os.path.join(self.setting('ErrorMessagesDir'), self.errorPageFilename()))
		f = open(filename, 'w')
		f.write(html)
		f.close()
		return filename

	def errorPageFilename(self):
		''' Construct a filename for an HTML error page, not including the 'ErrorMessagesDir' setting. '''
		return 'Error-%s-%s-%d.html' % (
			self.basicServletName(),
			string.join(map(lambda x: '%02d' % x, localtime(self._res.endTime())[:6]), '-'),
			whrandom.whrandom().randint(10000, 99999))
			# @@ 2000-04-21 ce: Using the timestamp & a random number is a poor technique for filename uniqueness, but this works for now

	def logExceptionToDisk(self, errorMsgFilename=''):
		''' Writes a tuple containing (date-time, filename, pathname, exception-name, exception-data,error report filename) to the errors file (typically 'Errors.csv') in CSV format. Invoked by handleException(). '''
		logline = (
			asctime(localtime(self._res.endTime())),
			self.basicServletName(),
			self.servletPathname(),
			str(self._exc[0]),
			str(self._exc[1]),
			errorMsgFilename)
		filename = self._app.serverSidePath(self.setting('ErrorLogFilename'))
		if os.path.exists(filename):
			f = open(filename, 'a')
		else:
			f = open(filename, 'w')
			f.write('time,filename,pathname,exception name,exception data,error report filename\n')
		logline = map(lambda element: str(element), logline)
		f.write(string.join(logline, ','))
		f.write('\n')
		f.close()

	def emailException(self, html):
		# Construct the message
		headers = self.setting('ErrorEmailHeaders')
		msg = []
		for key, value in headers.items():
			if isinstance(value, types.ListType):
				value = string.join(value, ', ')
			msg.append('%s: %s\n' % (key, value))
		msg.append('Date: %s\n' % dateForEmail())
		msg.append('\n')
		msg.append(html)
		msg = string.join(msg, '')

		# dbg code, in case you're having problems with your e-mail
		# open('error-email-msg.text', 'w').write(msg)

		# Send the message
		import smtplib
		server = smtplib.SMTP(self.setting('ErrorEmailServer'))
		server.set_debuglevel(0)
		server.sendmail(headers['From'], headers['To'], msg)
		server.quit()


# Some misc functions
def htTitle(name):
	return '''
<p> <br> <table border=0 cellpadding=4 cellspacing=0 bgcolor=#A00000> <tr> <td>
	<font face="Tahoma, Arial, Helvetica" color=white> <b> %s </b> </font>
</td> </tr> </table>''' % name


def osIdTable():
	''' Returns a list of dictionaries contained id information such as uid, gid, etc.,
		all obtained from the os module. Dictionary keys are 'name' and 'value'. '''
	funcs = ['getegid', 'geteuid', 'getgid', 'getpgrp', 'getpid', 'getppid', 'getuid']
	table = []
	for funcName in funcs:
		if hasattr(os, funcName):
			value = getattr(os, funcName)()
			table.append({'name': funcName, 'value': value})
	return table

def htTable(listOfDicts, keys=None):
	''' The listOfDicts parameter is expected to be a list of dictionaries whose keys are always the same.
		This function returns an HTML string with the contents of the table.
		If keys is None, the headings are taken from the first row in alphabetical order.
		Returns an empty string if listOfDicts is none or empty.
		Deficiencies: There's no way to influence the formatting or to use column titles that are different than the keys. '''

	if not listOfDicts:
		return ''

	if keys is None:
		keys = listOfDicts[0].keys()
		keys.sort()

	s = '<table border=0 cellpadding=2 cellspacing=2 bgcolor=#F0F0F0>\n<tr>'
	for key in keys:
		s = '%s<td><b>%s</b></td>' % (s, key)
	s = s + '</tr>\n'

	for row in listOfDicts:
		s = s + '<tr>'
		for key in keys:
			s = '%s<td>%s</td>' % (s, row[key])
		s = s + '</tr>\n'

	s = s + '</table>'
	return s

def dateForEmail():
    """ Returns a properly formatted date/time string for email messages """
    # @@ gat: this should be moved to MiscUtils
    now = time.localtime(time.time())
    if now[8] == 1:
        offset = -time.altzone / 60
    else:
        offset = -time.timezone / 60
    if offset<0:
        plusminus = '-'
    else:
        plusminus = '+'
    return time.strftime('%a, %d %b %Y %H:%M:%S ', now) + plusminus + '%02d%02d' % (abs(offset/60), abs(offset%60))

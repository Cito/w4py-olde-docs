from Page import Page
import string, os


class ExamplePage(Page):

	def title(self):
		return Page.title(self) + ' (WebKit Example)'

	def htTitle(self):
		return Page.title(self)

	def isDebugging(self):
		return 0

	def writeHeader(self):
		self.write('''
<head>
	<title>%s</title>
</head>
<body %s>''' % (self.title(), self.htBodyArgs()))
		self.writeBanner()
		self.writeExamplesToolBar()

	def writeBanner(self):
		self.writeln('''<table align=center bgcolor=darkblue cellpadding=5 cellspacing=0 width=100%%>
			<tr><td align=center>
				<font face="Tahoma, Arial, Helvetica" color=white><b>
					WebKit Examples
					<br><font size=+2>%s</font>
				</b></font>
			</td></tr>
		</table><p>''' % self.htTitle())

	def writeExamplesToolBar(self):
		hidden = ['ExamplePage']
		scripts = filter(lambda script, hidden=hidden: not script['name'] in hidden, self.scripts())
		scripts = map(lambda scriptDict: '<a href="%s">%s</a>' % (scriptDict['name'], scriptDict['name']), scripts)
		self.writeln('<p><center>', string.join(scripts, ' | '), '</center>')
		#handle case of which directory the client thinks we're in
		self.write('<p><center> <a href="')
		if string.find(self._request._environ['PATH_INFO'],'/Examples/')>0: self.write('../')
		self.writeln('PSPExamples/Hello.psp">PSP</a></center>')
		#end special case
		if self.isDebugging():
			self.writeln('<p><center>', self._session.identifier(), '</center>')
			from WebUtils.WebFuncs import HTMLEncode
			self.writeln('<p><center>', HTMLEncode(str(self._request.cookies())), '</center>')

	def scripts(self):
		# Create a list of dictionaries, where each dictionary stores information about
		# a particular script.
		from stat import *
		scripts = []
		dir = self._request.serverSideDir()
		examples = eval(open(self._request.relativePath('Examples.list'), 'r').read())
		for filename in map(lambda x: x+'.py', examples):
			if len(filename)>3  and  filename[-3:]=='.py':
				script = {}
				script['pathname'] = os.path.join(dir, filename)
				script['name']     = filename[:-3]
				scripts.append(script)
		return scripts

	def writeFooter(self):
		self.writeln('<p><br><hr>')
		self.writeln('<center>')

		# View the source of the current servlet
		self.write('<br><a href=View?filename=%s>source</a>' % self.__class__.__name__)

		# WebKit docs
		filename = 'Documentation/WebKit.html'
		if os.path.exists(filename):
			self.write(' | <a href=%s>%s</a>' % (filename, 'WebKit Docs'))

		# Webware docs
#		filename = '../Documentation/Webware.html'
#		if os.path.exists(filename):
#			self.write(' | <a href=%s>%s</a>' % (filename, 'Webware Docs'))

		# admin
		self.write(' | <a href=../Admin/>Admin</a>')

		# Project page
		self.write(' | <a href=http://webware.sourceforge.net>http://webware.sourceforge.net</a>')

		# Kit and versions
		self.write('<br>WebKit 0.3, part of Webware for Python 0.3') # @@ 2000-06-02 ce: should pick these up dynamically

		self.writeln('</center>')

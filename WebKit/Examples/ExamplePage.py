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
		self.writeHeaderLinks()

	def writeBanner(self):
		self.writeln('''<table align=center bgcolor=darkblue cellpadding=5 cellspacing=0 width=100%%>
			<tr><td align=center>
				<font face="Tahoma, Arial, Helvetica" color=white><b>
					WebKit Examples
					<br><font size=+2>%s</font>
				</b></font>
			</td></tr>
		</table><p>''' % self.htTitle())

	def writeHeaderLinks(self):
		scripts = self.scripts()
		root = self.request().uriWebKitRoot()
		scripts = map(lambda scriptDict: '<a href="%s">%s</a>' % (
			scriptDict['pathname'], scriptDict['name']), scripts)
		self.writeln('<p><center>', string.join(scripts, ' | '), '</center>')

		# handle case of which directory the client thinks we're in
		self.write('<p><center> <a href="')
		#if string.find(self._request._environ['PATH_INFO'],'/Examples/')>0: self.write('../')
		self.writeln(self.request().uriWebKitRoot() + 'PSPExamples/Hello.psp">PSP</a></center>')
		# end special case

		# Contexts
		adapterName = self.request().adapterName()
		ctxs = self.application().contexts().keys()
		ctxs = filter(lambda ctx: ctx!='default', ctxs)
		ctxs.sort()
		ctxs = map(lambda ctx, an=adapterName: '<a href=%s/%s/>%s</a> ' % (an, ctx, ctx), ctxs)
		self.writeln('<p><center>Contexts: ', string.join(ctxs, ' | '), '</center>')

		if self.isDebugging():
			self.writeln('<p><center>', self._session.identifier(), '</center>')
			from WebUtils.WebFuncs import HTMLEncode
			self.writeln('<p><center>', HTMLEncode(str(self._request.cookies())), '</center>')

		self.writeln('<hr>')

	def scripts(self):
		# Create a list of dictionaries, where each dictionary stores information about
		# a particular script.
		from stat import *
		import os
		scripts = []
		#dir = self._request.serverSideDir()
		dir = self._request.uriWebKitRoot() + "Examples"
		examples = eval(open(os.path.join(self.application()._serverDir,'Examples','Examples.list')).read())  #eval(open(self._request.relativePath('Examples.list'), 'r').read())
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
		viewpath = self._request.uriWebKitRoot() + "Examples/"+"View"
		self.write('<br><a href=%s?filename=%s>source</a>' % (viewpath,self.request().serverSidePath()))#self.__class__.__name__)

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
		self.write('<br>WebKit 0.4pre, part of Webware for Python 0.4pre') # @@ 2000-06-02 ce: should pick these up dynamically

		self.writeln('</center>')

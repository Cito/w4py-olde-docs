import os
from Page import Page


class AdminPage(Page):
	'''
	AdminPage is the abstract superclass of all WebKit administration CGI classes.

	@@ 2000-05-01 ce: update docs

	Subclasses typically override title() and writeBody(), but may customize other methods.

	Subclasses use self._var for the various vars that are passed in from CGI Wrapper
	and self.write() and self.writeln().
	'''

	## Content methods ##

	def writeHeader(self):
		self.writeln('''<html>
			<head>
				<title>%s</title>
			</head>
			<body %s><table align=center><tr><td>''' % (self.title(), self.htBodyArgs()))
		self.writeBanner()
		self.writeToolbar()

	def writeBanner(self):
		self.writeln('''<table align=center bgcolor=darkblue cellpadding=5 cellspacing=0 width=100%%>
			<tr><td align=center>
				<font face="Tahoma, Arial, Helvetica" color=white><b>
					WebKit AppServer
					<br><font size=+2>%s</font>
				</b></font>
			</td></tr>
		</table><p>''' % self.htTitle())

	def writeToolbar(self):
		pass

	def writeFooter(self):
		self.writeln('<p><br><hr>')
		self.writeln('<center>')

		# WebKit barfs on non-servlet files right now.

		# WebKit docs
#		filename = 'Documentation/WebKit.html'
#		if os.path.exists(filename):
#			self.write('<a href=%s>%s</a>' % (filename, 'WebKit'))

		# Webware docs
#		filename = '../Documentation/Webware.html'
#		if os.path.exists(filename):
#			self.write(' | <a href=%s>%s</a>' % (filename, 'Webware'))

		# Project page
		self.write(' <a href=http://webware.sourceforge.net>http://webware.sourceforge.net</a>')

		# Kit and versions
		self.write('<br>WebKit 0.3, part of Webware for Python 0.3')

		self.writeln('</center></table></body>')

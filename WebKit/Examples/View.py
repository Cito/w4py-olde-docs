import string
from ExamplePage import ExamplePage


class View(ExamplePage):
	"""
	At the bottom of each example you'll see a series of links, the
	first of which is called <b>source</b>. This link points to the
	View servlet and passes the filename of the current servlet. The
	View servlet then loads that file's source code and displays it
	in the browser for your viewing pleasure.
	<p>
	BTW, if the View servlet isn't passed a filename, it prints the
	View's doc string which you are reading right now.
	"""

	def writeBody(self):
		req = self.request()
		if not req.hasField('filename'):
			self.writeln('<p>', self.__class__.__doc__)
		else:
##			if req.hasField('tabSize'):
##				tabSize = int(req.field('tabSize'))
##			else:
##				tabSize = 4
##			filename = req.relativePath(req.field('filename')+'.py')
##			contents = open(filename).read()
##			if tabSize>0:
##				contents = string.expandtabs(contents, tabSize)
##			contents = string.replace(contents, '&', '&amp;')
##			contents = string.replace(contents, '<', '&lt;')
##			contents = string.replace(contents, '>', '&gt;')
##			self.writeln('<br><i>%s</i><hr><pre>%s</pre>' % (filename, contents))
			trans = self.transaction()
			trans.application().forwardRequest(trans, "Colorize.py")

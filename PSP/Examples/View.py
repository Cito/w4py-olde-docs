import string
from WebKit.Page import Page
import os

class View(Page):
	"""

	"""

	def writeBody(self):
		req = self.request()
		if req.hasField('filename'):
			self.writeln('<p>', self.__class__.__doc__)

			filename = req.field('filename')

			filename = self.request().serverSidePath(os.path.basename(filename))
			if not os.path.exists(filename):
				self.write("No such file %s exists" % filename)
				return

			text = open(filename).read()

			text = string.replace(text,"<","&lt;")
			text = string.replace(text,">","&gt;")
			text = string.replace(text,'\n',"<br>")

			self.write(text)
			

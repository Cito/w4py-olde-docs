from Page import Page
from WebUtils.WebFuncs import HTMLEncode
from types import *


class PlugInInspector(Page):
	def writeBody(self):
		for pi in self.application().server().plugIns():
			for item in [pi, dir(pi), '__name__', '__file__', '__path__']:
				if type(item) is StringType:
					item = (item, getattr(pi, item))
				self.writeln('<br> %s' % (HTMLEncode(str(item))))
			self.writeln('<hr>')


from StorePage import StorePage
from WebUtils.WebFuncs import URLEncode


class BrowseClasses(StorePage):

	def writeContent(self):
		self.writeln('Click a class on the left to browse all objects of that class.')

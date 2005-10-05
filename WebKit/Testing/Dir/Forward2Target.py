from WebKit.Page import Page

class Forward2Target(Page):

	def writeContent(self):
		self.writeln('<h2><tt>%s</tt></h2>' % self.__class__.__name__ )
		self.writeln('<pre>%s</pre>' % self.request().getstate() )

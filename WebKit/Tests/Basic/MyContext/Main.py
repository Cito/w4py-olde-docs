
from WebKit.Page import Page

class Main(Page):

	def title(self):
		return 'My Sample Context'

	def writeContent(self):
		self.writeln('<h1>Welcome to Webware!</h1>')
		self.writeln('''
		This is a sample context generated for you and has purposly been kept very simple
		to give you something to play with to get yourself started.  The code that implements
		this page is located in <b>%s</b>.
		''' % self.request().serverSidePath())

		self.writeln('''
		<p>
		There are more examples and documentaion in the Webware distribution, which you
		can get to from here:<p><ul>
		''')

		adapterName = self.request().adapterName()
		ctxs = self.application().contexts().keys()
		ctxs = filter(lambda ctx: ctx!='default', ctxs)
		ctxs.sort()
		for ctx in ctxs:
			self.writeln('<li><a href="%s/%s/">%s</a>' % (adapterName, ctx, ctx))

		self.writeln('</ul>')


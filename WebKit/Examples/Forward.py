from ExamplePage import ExamplePage

class Forward(ExamplePage):

	def writeBody(self):
		trans = self.transaction()
		resp = self.response()
		resp.write("""<p>I am forwarding this request to the Welcome Servlet.  You'll see it's output below in bold blue.<p><b><font color=blue>""")
		trans.application().forwardRequest(trans, 'Welcome.py')
		resp.write("""</font></b>""")


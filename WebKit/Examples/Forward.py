from ExamplePage import ExamplePage

class Forward(ExamplePage):

	def writeBody(self):

		self._response.write("""<p>I am forwarding this request to the Welcome Servlet.  You'll see it's output below
		in bold blue.<p><b><font color='blue'>""")
		self._transaction.application().forwardRequest(self._transaction,'Welcome.py')
		self._response.write("""</font></b>""")
		

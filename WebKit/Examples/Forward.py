from ExamplePage import ExamplePage

class Forward(ExamplePage):

	def writeBody(self):
		trans = self.transaction()
		resp = self.response()
		resp.write("<p>This is the Forward servlet speaking. I am now going to forward the request to the Welcome servlet via Application's forwardRequest() method:<br><p>")
		trans.application().forwardRequest(trans, 'Welcome.py')

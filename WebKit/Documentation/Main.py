from HTTPServlet import HTTPServlet


class Main(HTTPServlet):

	def respond(self, trans):
		trans.application().forwardRequest(trans, 'WebKit.html')

from WebKit.HTTPServlet import HTTPServlet


class index(HTTPServlet):

	def respond(self, trans):
		trans.application().forwardRequest(trans, 'Welcome')
#		trans.response().sendRedirect('Welcome')

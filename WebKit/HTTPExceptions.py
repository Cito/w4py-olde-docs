from types import *
from WebUtils.Funcs import htmlEncode

True, False = 1==1, 0==1

class HTTPException(Exception):

	"""
	Subclasses must define these variables (usually as class
	variables):
	_code: a tuple of the integer error code, and the short
	    description that goes with it (like (200, "OK"))
	_description: the long-winded description, to be presented
	    in the response page.  Or you can override description().
	"""

	_description = 'An error occurred'

	def code(self):
		return self._code[0]

	def codeMessage(self):
		return self._code[1]

	def html(self):
		return '''
<html><head><title>%(code)s %(title)s</title></head>
<body>
<h1>%(title)s</h1>
%(body)s
</body></html>''' % {
			"title": self.htTitle(),
			"body": self.htBody(),
			"code": self.code()
			}

	def title(self):
		return self.codeMessage()

	def htTitle(self):
		return self.title()

	def htBody(self):
		body = self.htDescription()
		if self.args:
			body += ''.join(['<p>%s</p>\n' % str(l) for l in self.args])
		return body

	def headers(self):
		return {}

	def title(self):
		return self.codeMessage()

	def description(self):
		return self._description

	def htDescription(self):
		return self.description()

	def setTransaction(self, trans):
		self._transaction = trans


class HTTPNotImplemented(HTTPException):
	_code = 501, "Not Implemented"
	_description = "The method given is not yet implemented by this application"

class HTTPForbidden(HTTPException):
	_code = 403, 'Forbidden'
	_description = "You are not authorized to access this resource"

class HTTPAuthenticationRequired(HTTPException):
	_code = 401, 'Authentication Required'
	_description = "You must log in to access this resource"
	def __init__(self, realm=None, *args):
		if not realm:
			realm = 'Password required'
		assert realm.find('"') == -1, 'Realm must not contain "'
		self._realm = realm
		HTTPException.__init__(self, *args)

	def headers(self):
		return {'WWW-Authenticate': 'Basic realm="%s"' % self._realm}

## This is for wording mistakes.  I'm unsure about their benefit.
HTTPAuthorizationRequired = HTTPAuthenticationRequired

class HTTPMethodNotAllowed(HTTPException):
	_code = 405, 'Method Not Allowed'
	_description = 'The method is not supported on this resource'

class HTTPConflict(HTTPException):
	_code = 409, 'Conflict'

class HTTPUnsupportedMediaType(HTTPException):
	_code = 415, 'Unsupported Media Type'

class HTTPInsufficientStorage(HTTPException):
	_code = 507, 'Insufficient Storage'
	_description = 'There was not enough storage space on the server to complete your request'

class HTTPPreconditionFailed(HTTPException):
	_code = 412, 'Precondition Failed'

class HTTPMovedPermanently(HTTPException):
	_code = 301, 'Moved Permanently'
	
	def __init__(self, location=None, webkitLocation=None, *args):
		self._location = location
		self._webkitLocation = webkitLocation
		HTTPException.__init__(self, 301, 'Moved Permanently', *args)

	def location(self):
		if self._webkitLocation:
			environ = self._transaction.request().environ()
			if not self._webkitLocation.startswith('/'):
				self._webkitLocation = '/' + self._webkitLocation
			location = 'http://%s%s%s' % (
				environ.get('HTTP_HOST', environ['SERVER_NAME']),
				environ['SCRIPT_NAME'],
				self._webkitLocation)
		else:
			location = self._location
		return location

	def headers(self):
		return {'Location': self.location()}

	def description(self):
		return 'The resource you are accessing has been moved to <a href="%s">%s</a>' % (htmlEncode(self.location()), htmlEncode(self.location()))

class HTTPTemporaryRedirect(HTTPMovedPermanently):

	_code = 307, 'Temporary Redirect'

# This is what people mean most often:
HTTPRedirect = HTTPTemporaryRedirect

class HTTPBadRequest(HTTPException):
	_code = 400, 'Bad Request'

class HTTPNotFound(HTTPException):
	_code = 404, 'Not Found'
	_description = 'The resource you were trying to access was not found'

from Common import *
from Response import Response
from Cookie import Cookie


class HTTPResponse(Response):


	## Init ##

	def __init__(self, headers=None):
		''' Initializes the request. '''

		Response.__init__(self)

		if headers is None:
			self._headers = {'Content-type': 'text/html'}
		else:
			self._headers = headers

		self._cookies   = {}
		self._committed = 0
		self._contents  = []


	## Headers ##

	def header(self, name, default=Tombstone):
		''' Returns the value of the specified header. '''
		if default is Tombstone:
			return self._headers[name]
		else:
			return self._headers.get(name, default)

	def hasHeader(self):
		return self._headers.has_key(name)

	def setHeader(self, name, value):
		''' Sets a specific header by name. '''
		assert self._committed==0
		self._headers[name] = value

	def addHeader(self, name, value):
		''' Adds a specific header by name. '''
		assert self._committed==0
		raise NotImplementedError

	def headers(self, name=None):
		''' Returns a dictionary-style object of all Header objects contained by this request. '''
		return self._headers

	def clearHeaders(self):
		''' Clears all the headers. You might consider a setHeader('Content-type', 'text/html') or something similar after this. '''
		assert self._committed==0
		self._headers = {}


	## Cookies ##

	def cookie(self, name):
		''' Returns the value of the specified cookie. '''
		return self._cookies[name]

	def hasCookie(self, name):
		return self._cookies.has_key(name)

	def setCookie(self, name, value):
		''' Sets the named cookie to a value. '''
		assert self._committed==0
		self.addCookie(Cookie(name, value))

	def addCookie(self, cookie):
		''' Adds a cookie that will be sent with this response. '''
		assert self._committed==0
		assert isinstance(cookie, Cookie)
		self._cookies[cookie.name()] = cookie

	def cookies(self):
		''' Returns a dictionary-style object of all Cookie objects that will be sent with this response. '''
		return self._cookies

	def clearCookies(self):
		''' Clears all the cookies. '''
		assert self._committed==0
		self._cookies = {}


	## Status ##

	def setStatus(self, code):
		''' Set the status code of the response, such as 200, 'OK'. '''
		assert self._committed==0
		self.setHeader('Status', code)


	## Special responses ##

	def sendError(self, code, msg=None):
		assert self._committed==0
		raise NotImplementedError

	def sendRedirect(self, url):
		''' This method sets the headers and content for the redirect, but does NOT change the cookies. Use clearCookies() as appropriate. '''
		assert self._committed==0
		self._headers = {'Location': url, 'Content-type': 'text/html'}
		self._contents = [
			'<html> <body> This page has been redirected to <a href="%s">%s</a>. </body> </html>' % (url, url)]


	## Output ##

	def write(self, string):
		assert self._committed==0
		self._contents.append(str(string))

	def isCommitted(self):
		return self._committed

	def deliver(self, trans):
		self.recordSession(trans)
		self._contents = string.join(self._contents, '')
		self.recordEndTime()
		self._committed = 1

	def recordSession(self, trans):
		''' Invoked by deliver() to record the session id in the response (if a session exists). This implementation sets a cookie for that purpose. For people who don't like sweets, a future version could check a setting and instead of using cookies, could parse the HTML and update all the relevant URLs to include the session id (which implies a big performance hit). Or we could require site developers to always pass their URLs through a function which adds the session id (which implies pain). Personally, I'd rather just use cookies. You can experiment with different techniques by subclassing Session and overriding this method. Just make sure Application knows which "session" class to use. '''
		sess = trans._session
		debug = 0
		if debug: prefix = '>> recordSession:'
		if sess:
			cookie = Cookie('_SID_', sess.identifier())
			cookie.setPath('/')
			self.addCookie(cookie)
			if debug: print prefix, 'setting sid =', sess.identifier()
		else:
			print prefix, 'did not set sid'

	def reset(self):
		''' Resets the response (such as headers, cookies and contents). '''
		self._committed = 0  # @@ 2000-06-09 ce: this fixes ExceptionHandler problem where it reuses the response. maybe this is "bad"
		self._headers = {'Content-type': 'text/html'}
		self._cookies = {}
		self._contents = []

	def rawResponse(self):
		''' Returns the final contents of the response. Don't invoke this method until after deliver().
		Returns a dictionary representing the response containing only strings, numbers, lists, tuples, etc. with no backreferences. That means you don't need any special imports to examine the contents and you can marshal it. Currently there are two keys. 'headers' is list of tuples each of which contains two strings: the header and it's value. 'contents' is a string (that may be binary (for example, if an image were being returned)). '''
		headers = []
		for key, value in self._headers.items():
			headers.append((key, value))
		for cookie in self._cookies.values():
			headers.append(('Set-Cookie', cookie.headerValue()))
		return {
			'headers': headers,
			'contents': self._contents
		}

	def size(self):
		''' Returns the size of the final contents of the response. Don't invoke this method until after deliver(). '''
		assert self._contents is not None, 'Contents are not set. Perhaps deliver() has not been invoked.'
		return len(self._contents)

	def appendRawResponse(self, rawRes):
		'''
		Appends the contents of the raw response (as returned by some transaction's rawResponse() method) to this response.
		The headers of the receiving response take precedence over the appended response.
		This method was built primarily to support Application.forwardRequest().
		'''
		assert self._committed==0
		headers = rawRes.get('headers', [])
		for key, value in headers:
			if not self._headers.has_key(key):
				self._headers[key] = value
		self.write(rawRes['contents'])

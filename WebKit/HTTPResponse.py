from Common import *
from Response import Response
from Cookie import Cookie
		

class HTTPResponse(Response):
	'''
	FUTURE
		* how to deal with auto-including the session id. this also should consider sendRedirect()
	'''

	## Init ##
	
	def __init__(self, headers=None):
		''' Initializes the request. You should pass the arguments by name rather than position. '''

		Response.__init__(self)

		if headers is None:
			self._headers = {'Content-type': 'text/html'}
		else:
			self._headers = headers
		
		self._cookies = {}
		self._committed = 0
		self._contents = []


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
		self._headers[name] = value
	
	def addHeader(self, name, value):
		''' Adds a specific header by name. '''
		raise NotImplementedError
		
	def headers(self, name=None):
		''' Returns a dictionary-style object of all Header objects contained by this request. '''
		return self._headers


	## Cookies ##
	
	def cookie(self, name):
		''' Returns the value of the specified cookie. '''
		return self._cookies[name]
	
	def hasCookie(self, name):
		return self._cookies.has_key(name)

	def setCookie(self, name, value):
		''' Sets the named cookie to a value. '''
		self.addCookie(Cookie(name, value))

	def addCookie(self, cookie):
		''' Adds a cookie that will be sent with this response. '''
		assert isinstance(cookie, Cookie)
		self._cookies[cookie.name()] = cookie

	def cookies(self):
		''' Returns a dictionary-style object of all Cookie objects that will be sent with this response. '''
		return self._cookies


	## Status ##
	
	def setStatus(self, code):
		raise NotImplementedError

		
	## Special responses ##
	
	def sendError(self, code, msg=None):
		raise NotImplementedError

	def sendRedirect(self, url):
		self._headers = {'Location': url}
		self._cookies = {}
		self._contents = []

		
	## Output ##
	
	def write(self, string):
		self._contents.append(str(string))
	
	def isCommitted(self):
		return self._committed

	def deliver(self, trans):
		self._committed = 1
		self.recordSession(trans)
		prefix = []
		for key, value in self._headers.items():
			prefix.append('%s: %s\n' % (key, value))
		for cookie in self._cookies.values():
			prefix.append('%s\n' % cookie.headerString())
		prefix.append('\n')
		self._contents = string.join(prefix, '') + string.join(self._contents, '')
		self.recordEndTime()

	def recordSession(self, trans):
		''' Invoked by deliver() to record the session id in the response (if a session exists). This implementation sets a cookie for that purpose. For people who don't like sweets, a future version could check a setting and instead of using cookies, could parse the HTML and update all the relevant URLs to include the session id (which implies a big performance hit). Or we could require site developers to always pass their URLs through a function which adds the session id (which implies pain). Personally, I'd rather just use cookies. You can experiment with different techniques by subclassing Session and overriding this method. Just make sure Application knows which "session" class to use. '''
		sess = trans.session()
		if sess:
			self.setCookie('_SID_', sess.identifier())

	def reset(self):
		''' Resets the response (such as headers, cookies and contents). '''
		self._headers = {'Content-type': 'text/html'}
		self._cookies = {}
		self._contents = []
	
	def contents(self):
		''' Returns the final contents of the response. Don't invoke this method until after deliver(). '''
		assert self._contents is not None, 'Contents are not set. Perhaps deliver() has not been invoked.'
		return self._contents

	def size(self):
		''' Returns the size of the final contents of the response. Don't invoke this method until after deliver(). '''
		assert self._contents is not None, 'Contents are not set. Perhaps deliver() has not been invoked.'
		return len(self._contents)

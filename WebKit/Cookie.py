from Common import *
import zCookieEngine


class Cookie(Object):
	'''
	Cookie is used to create cookies that have additional attributes beyond their value.
	
	Note that web browsers don't typically send any information with the cookie other than it's value. Therefore, in HTTPRequest, cookie() simply returns a value such as an integer or a string.

	When the server sends cookies back to the browser, it can send a cookie that simply has a value, or the cookie can be accompanied by various attributes (domain, path, max-age, ...) as described in RFC 2109. Therefore, in HTTPResponse, setCookie() can take either an instance of the Cookie class, as defined in this module, or a value.
	
	Note that Cookies values get pickled (see the pickle module), so you can set and get cookies that are integers, lists, dictionaries, etc.
		
	HTTP Cookies are officially described in RFC 2109:
	
		ftp://ftp.isi.edu/in-notes/rfc2109.txt
		
	FUTURE
	
		* This class should provide error checking in the setFoo() methods. Or maybe our internal Cookie implementation already does that?
		* This implementation is probably not as efficient as it should be, [a] it works and [b] the interface is stable. We can optimize later.		
	'''

	## Init ##

	def __init__(self, name, value):
		self._cookies = zCookieEngine.SmartCookie()
		self._name = name
		self._value = value
		self._cookies[name] = value
		self._cookie = self._cookies[name]


	## Access attributes ##

	def comment(self):
		return self._cookie['comment']

	def domain(self):
		return self._cookie['domain']

	def maxAge(self):
		return self._cookie['max-age']

	def name(self):
		return self._name

	def path(self):
		return self._cookie['path']
	
	def isSecure(self):
		return self._cookie['secure']
	
	def value(self):
		return self._value
	
	def version(self):
		return self._cookie['version']

		
	## Setting attributes ##

	def setComment(self, comment):
		self._cookie['comment'] = comment

	def setDomain(self, domain):
		self._cookie['domain'] = domain
	
	def setMaxAge(self, maxAge):
		self._cookie['max-age'] = maxAge
		
	def setPath(self, path):
		self._cookie['path'] = path
	
	def setSecure(self, bool):
		self._cookie['secure'] = bool
		
	def setValue(self, value):
		self._value = value
		self._cookies[self._name] = value

	def setVersion(self, version):
		self._cookie['version'] = version

	
	## HTTP Headers ##
	
	def headerString(self):
		return str(self._cookies)

from Common import *
from Request import Request
from WebUtils.Cookie import Cookie
import cgi
from types import ListType

class HTTPRequest(Request):
	'''
	FUTURE
		* How about some documentation?
		* The "Information" section is a bit screwed up. Because the WebKit server adaptor is a CGI script, these values are oriented towards that rather than the servlet.
	'''

	## Initialization ##

	def __init__(self, dict={}):
		if dict:
			# Dictionaries come in from web server adaptors like the CGIAdaptor
			from StringIO import StringIO
			assert dict['format']=='CGI'
			self._time    = dict['time']
			self._environ = dict['environ']
			self._input   = dict['input']
			self._fields  = cgi.FieldStorage(fp=StringIO(self._input), environ=self._environ, keep_blank_values=1, strict_parsing=0)
			self._cookies = Cookie()
			if self._environ.has_key('HTTP_COOKIE'):
				self._cookies.load(self._environ['HTTP_COOKIE'])
		else:
			# If there's no dictionary, we pretend we're a CGI script and see what happens...
			import time
			self._time    = time.time()
			self._environ = os.environ.copy()
			self._input   = ''
			self._fields  = cgi.FieldStorage(keep_blank_values=1)
			self._cookies = Cookie()

		# Fix up environ if it doesn't look right.
		# This happens when there is no extra path info past the adapter.
		# e.g., http://localhost/WebKit.cgi
		if not self._environ.has_key('PATH_INFO'):
			self._environ['PATH_INFO'] = '/'
			self._environ['PATH_TRANSLATED'] = self._environ['DOCUMENT_ROOT']

		# We use the cgi module to get the fields, but then change them into an ordinary dictionary of values
		dict = {}
		for key in self._fields.keys():
			value = self._fields[key]
			if type(value) is not ListType:
				value = value.value # i.e., if we don't have a list, we have one of those cgi.MiniFieldStorage objects. Get it's value.
			else:
				value = map(lambda miniFieldStorage: miniFieldStorage.value, value) # extract those .value's
			dict[key] = value
		self._fields = dict

		self._pathInfo = None

		# We use Tim O'Malley's Cookie class to get the cookies, but then change them into an ordinary dictionary of values
		dict = {}
		for key in self._cookies.keys():
			dict[key] = self._cookies[key].value
		self._cookies = dict

		self._serverSidePath = None
		self._serverSideDir  = None
		self._transaction    = None


	## Transactions ##

	def transaction(self):
		return self._transaction


	def setTransaction(self, trans):
		''' This method should be invoked after the transaction is created for this request. '''
		self._transaction = trans


	## Special ##

	def environ(self):
		return self._environ  # @@ 2000-05-01 ce: To implement ExceptionHandler.py


	## Values ##

	def value(self, name, default=Tombstone):
		''' Returns the value with the given name. Values are fields or cookies. Use this method when you're field/cookie agnostic. '''
		if self._fields.has_key(name):
			return self._fields[name]
		else:
			return self.cookie(name, default)

	def hasValue(self, name):
		return self._fields.has_key(name) or self._cookies.has_key(name)


	## Fields ##

	def field(self, name, default=Tombstone):
		if default is Tombstone:
			return self._fields[name]
		else:
			return self._fields.get(name, default)

	def hasField(self, name):
		return self._fields.has_key(name)

	def fields(self):
		return self._fields


	## Cookies ##

	def cookie(self, name, default=Tombstone):
		''' Returns the value of the specified cookie. '''
		if default is Tombstone:
			return self._cookies[name]
		else:
			return self._cookies.get(name, default)

	def hasCookie(self, name):
		return self._cookies.has_key(name)

	def cookies(self):
		''' Returns a dictionary-style object of all Cookie objects the client sent with this request. '''
		return self._cookies


	## Sessions ##

	def session(self):
		''' Returns the session associated with this request, either as specified by sessionId() or newly created. @@ 2000-05-10 ce: Not Implemented. '''
		raise NotImplementedError


	## Authentication ##

	def remoteUser(self):
		''' Always returns None since authentication is not yet supported. Take from CGI variable REMOTE_USER. '''
		# @@ 2000-03-26 ce: maybe belongs in section below. clean up docs
		return self._environ['REMOTE_USER']


	## Remote info ##

	def remoteAddress(self):
		''' Returns a string containing the Internet Protocol (IP) address of the client that sent the request. '''
		return self._environ['REMOTE_ADDR']

	def remoteName(self):
		''' Returns the fully qualified name of the client that sent the request, or the IP address of the client if the name cannot be determined. '''
		raise self.remoteName()


	## Path ##

	def serverSidePath(self):
		''' Returns the complete, unambiguous server-side path for the request. '''
		if self._serverSidePath is None:
			path = self._environ['PATH_INFO'][1:] #This is the path after FCGIWebKit.py, ie Hello.py or Hello.psp
			# The [1:] above strips the preceding '/' that we get with Apache 1.3
			app = self._transaction.application()
			self._serverSidePath = app.serverSidePathForRequest(self, path)
		return self._serverSidePath

	def serverSideDir(self):
		''' Returns the directory of the Servlet (as given through __init__()'s path). '''
		if self._serverSideDir is None:
			self._serverSideDir = os.path.split(self.serverSidePath())[0]
		return self._serverSideDir

	def relativePath(self, joinPath):
		''' Returns a new path which includes the servlet's path appended by 'joinPath'. Note that if 'joinPath' is an absolute path, then only 'joinPath' is returned. '''
		return os.path.join(self.serverSideDir(), joinPath)

	def servletURI(self):
		"""This is the URI of the servlet, without any query strings or extra path info"""

		sspath=self.serverSidePath()#ensure that extraPathInfo has been stripped
		pinfo=self.pathInfo()
		URI=pinfo[:string.rfind(pinfo,self.value("extraPathInfo",''))]
		if URI[-1]=="/": URI=URI[:-1]
		return URI




	## Information ##

	# @@ 2000-05-10: See FUTURE section of class doc string

	def servletPath(self):
		# @@ 2000-03-26 ce: document
		return self._environ['SCRIPT_NAME']

	def contextPath(self):
		''' Returns the portion of the request URI that is the context of the request. '''
		# @@ 2000-03-26 ce: this comes straight from Java servlets. Do we want this?
		raise NotImplementedError

	def pathInfo(self):
		''' Returns any extra path information associated with the URL the client sent with this request. Equivalent to CGI variable PATH_INFO. '''
		if self._pathInfo is None:
			self._pathInfo = self._environ['PATH_INFO'][1:]
			# The [1:] above strips the preceding '/' that we get with Apache 1.3
		return self._pathInfo

	def pathTranslated(self):
		''' Returns any extra path information after the servlet name but before the query string, translated to a file system path. Equivalent to CGI variable PATH_TRANSLATED. '''
#		return self._environ['PATH_TRANSLATED']
# @@ 2000-06-22 ce: resolve this
		return self._environ.get('PATH_TRANSLATED', None)

	def queryString(self):
		''' Returns the query string portion of the URL for this request. Taken from the CGI variable QUERY_STRING. '''
		return self._environ['QUERY_STRING']

	def uri(self):
		''' Returns the request URI, which is the entire URL except for the query string. '''
		return self._environ['REQUEST_URI']

	def method(self):
		''' Returns the HTTP request method (in all uppercase), typically from the set GET, POST, PUT, DELETE, OPTIONS and TRACE. '''
		return string.upper(self._environ['REQUEST_METHOD'])

	def sessionId(self):
		''' Returns a string with the session id specified by the client, or None if there isn't one. '''
		return self.value('_SID_', None)


	## Inspection ##

	def info(self):
		''' Returns a list of tuples where each tuple has a key/label (a string) and a value (any kind of object). Values are typically atomic values such as numbers and strings or another list of tuples in the same fashion. This is for debugging only. '''
		# @@ 2000-04-10 ce: implement and invoke super if appropriate
		info = [
			('time',    self._time),
			('environ', self._environ),
			('input',   self._input),
			('fields',  self._fields),
			('cookies', self._cookies)
		]

		# Information methods
		for method in _infoMethods:
			info.append((method.__name__, apply(method, (self,))))

		return info

	def htmlInfo(self):
		''' Returns a single HTML string that represents info(). Useful for inspecting objects via web browsers. '''
		return htmlInfo(self.info())
		info = self.info()
		res = ['<table border=1>\n']
		for pair in info:
			value = pair[1]
			if hasattr(value, 'items') and (type(value) is type({}) or hasattr(value, '__getitem__')):
				value = _infoForDict(value)
			res.append('<tr valign=top> <td> %s </td>  <td> %s&nbsp;</td> </tr>\n' % (pair[0], value))
		res.append('</table>\n')
		return string.join(res, '')


_infoMethods = (
	HTTPRequest.servletPath,
	HTTPRequest.contextPath,
	HTTPRequest.pathInfo,
	HTTPRequest.pathTranslated,
	HTTPRequest.queryString,
	HTTPRequest.uri,
	HTTPRequest.method,
	HTTPRequest.sessionId
)


def htmlInfo(info):
	''' Returns a single HTML string that represents the info structure. Useful for inspecting objects via web browsers. '''
	res = ['<table border=1>\n']
	for pair in info:
		value = pair[1]
		if hasattr(value, 'items') and (type(value) is type({}) or hasattr(value, '__getitem__')):
			value = htmlInfo(_infoForDict(value))
		res.append('<tr valign=top> <td> %s </td>  <td> %s&nbsp;</td> </tr>\n' % (pair[0], value))
	res.append('</table>\n')
	return string.join(res, '')

def _infoForDict(dict):
	''' Returns an "info" structure for any dictionary-like object. '''
	items = dict.items()
	items.sort(lambda a, b: cmp(a[0], b[0]))
	return items

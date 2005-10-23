"""WebUtils.Funcs

This module provides some basic functions that are useful
in HTML and web development.

You can safely import * from WebUtils.Funcs if you like.

TO DO

* Document the 'codes' arg of htmlEncode/Decode.

"""


htmlForNone = '-'  # used by htmlEncode.

htmlCodes = [
	['&', '&amp;'],
	['<', '&lt;'],
	['>', '&gt;'],
	['"', '&quot;'],
#	['\n', '<br>']
]

htmlCodesReversed = htmlCodes[:]
htmlCodesReversed.reverse()

def htmlEncode(what, codes=htmlCodes):
	if what is None:
		return htmlForNone
	if hasattr(what, 'html'):
		# allow objects to specify their own translation to html
		# via a method, property or attribute
		ht = what.html
		if callable(ht):
			ht = ht()
		return ht
	what = str(what)
	return htmlEncodeStr(what, codes)

def htmlEncodeStr(s, codes=htmlCodes):
	"""Return the HTML encoded version of the given string.

	This is useful to display a plain ASCII text string on a web page.

	"""
	for code in codes:
		s = s.replace(code[0], code[1])
	return s

def htmlDecode(s, codes=htmlCodesReversed):
	"""Return the ASCII decoded version of the given HTML string.

	This does NOT remove normal HTML tags like <p>.
	It is the inverse of htmlEncode().

	"""
	for code in codes:
		s = s.replace(code[1], code[0])
	return s

_urlEncode = {}
for i in range(256):
	_urlEncode[chr(i)] = '%%%02X' % i
from string import letters, digits
for c in letters + digits + '_.-/':
	_urlEncode[c] = c
_urlEncode[' '] = '+'

def urlEncode(s):
	"""Return the encoded version of the given string, safe for using as a URL."""
	return ''.join(map(lambda c: _urlEncode[c], s))

def urlDecode(s):
	"""Return the decoded version of the given string.

	Note that invalid URLs will throw exceptons.
	For example, a URL whose % coding is incorrect.

	"""
	p1 = s.replace('+', ' ').split('%')
	p2 = [p1.pop(0)]
	for p in p1:
		p2.append(chr(int(p[:2], 16)) + p[2:])
	return ''.join(p2)

def htmlForDict(dict, addSpace=None, filterValueCallBack=None, maxValueLength=None):
	"""Return an HTML string with a <table> where each row is a key-value pair."""
	keys = dict.keys()
	keys.sort()
	# A really great (er, bad) example of hardcoding.  :-)
	html = ['<table width="100%" border="0" cellpadding="2" cellspacing="2"'
		' style="background-color:#FFFFFF;font-size:10pt">']
	for key in keys:
		value = dict[key]
		if addSpace!=None  and  addSpace.has_key(key):
			target = addSpace[key]
			value = target.join(value.split(target))
		if filterValueCallBack:
			value = filterValueCallBack(value, key, dict)
		value = str(value)
		if maxValueLength and len(value) > maxValueLength:
			value = value[:maxValueLength] + '...'
		html.append('<tr>'
			'<td style="background-color:#F0F0F0">%s</td>'
			'<td style="background-color:#F0F0F0">%s &nbsp;</td></tr>\n'
			% (htmlEncode(str(key)), htmlEncode(value)))
	html.append('</table>')
	return ''.join(html)

def requestURI(dict):
	"""Return the request URI for a given CGI-style dictionary.

	Uses REQUEST_URI if available, otherwise constructs and returns it
	from SCRIPT_NAME, PATH_INFO and QUERY_STRING.

	"""
	uri = dict.get('REQUEST_URI', None)
	if uri == None:
		uri = dict.get('SCRIPT_NAME', '') + dict.get('PATH_INFO', '')
		query = dict.get('QUERY_STRING', '')
		if query != '':
			uri = uri + '?' + query
	return uri

def normURL(path):
	"""Normalizes a URL path, like os.path.normpath.

	Acts on	a URL independant of operating system environment.

	"""
	if not path:
		return
	initialslash = path[0] == '/'
	lastslash = path[-1] == '/'
	comps = '/'.split(path)
	newcomps = []
	for comp in comps:
		if comp in ('','.'):
			continue
		if comp != '..':
			newcomps.append(comp)
		elif newcomps:
			newcomps.pop()
	path = '/'.join(newcomps)
	if path and lastslash:
		path = path + '/'
	if initialslash:
		path = '/' + path
	return path

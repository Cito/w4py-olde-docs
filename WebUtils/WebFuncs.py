'''
WebUtils.py
Webware for Python
Last updated: 4/6/2000

WebUtils provides some basic functions that are useful in HTML and CGI development.

You can safely import * from WebUtils if you like.


TO DO

* Document the 'codes' arg of HTMLEncode/Decode.

'''

import string


HTMLCodes = [
	['&', '&amp;'],
	['<', '&lt;'],
	['>', '&gt;'],
	['"', '&quot;'],
#	['\n', '<br>']
]

HTMLCodesReversed = HTMLCodes[:]
HTMLCodesReversed.reverse()


def HTMLEncode(s, codes=HTMLCodes):
	''' Returns the HTML encoded version of the given string. This is useful to display a plain ASCII text string on a web page.'''
	for code in codes:
		s = string.replace(s, code[0], code[1])
	return s

def HTMLDecode(s, codes=HTMLCodesReversed):
	''' Returns the ASCII decoded version of the given HTML string. This does NOT remove normal HTML tags like <p>. It is the inverse of HTMLEncode(). '''
	for code in codes:
		s = string.replace(s, code[1], code[0])
	return s



_URLEncode = {}
for i in range(256):
	_URLEncode[chr(i)] = '%%%02x' % i
for c in string.letters + string.digits + '_,.-/':
	_URLEncode[c] = c
_URLEncode[' '] = '+'

def URLEncode(s):
	''' Returns the encoded version of the given string, safe for using as a URL. '''
	return string.join(map(lambda c: _URLEncode[c], list(s)), '')

def URLDecode(s):
	''' Returns the decoded version of the given string. Note that invalid URLs will throw exceptons. For example, a URL whose % coding is incorrect. '''
	mychr = chr
	atoi = string.atoi
	parts = string.split(string.replace(s, '+', ' '), '%')
	for i in range(1, len(parts)):
		part = parts[i]
		parts[i] = mychr(atoi(part[:2], 16)) + part[2:]
	return string.join(parts, '')


def HTMLForDictionary(dict, addSpace=None):
	''' Returns an HTML string with a <table> where each row is a key-value pair. '''
	keys = dict.keys()
	keys.sort()
	# A really great (er, bad) example of hardcoding.  :-)
	html = ['<table width=100% border=0 cellpadding=2 cellspacing=2>']
	for key in keys:
		value = dict[key]
		if addSpace!=None  and  addSpace.has_key(key):
			target = addSpace[key]
			value = string.join(string.split(value, target), '%s '%target)
		html.append('<tr bgcolor=#F0F0F0> <td> %s </td> <td> %s &nbsp;</td> </tr>\n' % (key, value))
	html.append('</table>')
	return string.join(html, '')



"""
This module defines a subClass of the standard python cgi.FieldStorage class with an extra method that will allow a FieldStorage to parse a query string even in a POST request.
"""


import cgi, os, urllib, string

class FieldStorage(cgi.FieldStorage):

	def __init__(self, fp=None, headers=None, outerboundary="",
                 environ=os.environ, keep_blank_values=0, strict_parsing=0):
		self._environ = environ
		cgi.FieldStorage.__init__(self, fp, headers, outerboundary, environ, keep_blank_values, strict_parsing)
	
	def parse_qs(self):
		"""
		Explicitly parse the query string, even if it's a POST request
		"""
		self._method = string.upper(self._environ['REQUEST_METHOD'])
		if self._method == "GET" or  self._method == "HEAD":
##			print __file__, "bailing on GET or HEAD request"
			return  #bail because cgi.FieldStorage already did this
		self._qs = self._environ.get('QUERY_STRING', None)
		if self._qs: self._qs = string.upper(self._qs)
		else:
			print __file__, "bailing on no query_string"
			return  ##bail if no query string


		name_value_pairs = string.splitfields(self._qs, '&')
		dict = {}
		for name_value in name_value_pairs:
			nv = string.splitfields(name_value, '=')
			if len(nv) != 2:
				if strict_parsing:
					raise ValueError, "bad query field: %s" % `name_value`
				continue
			name = urllib.unquote(string.replace(nv[0], '+', ' '))
			value = urllib.unquote(string.replace(nv[1], '+', ' '))
			if len(value) or keep_blank_values:
				if dict.has_key (name):
					dict[name].append(value)
					print "appending"
				else:
					dict[name] = [value]
					print "no append"


		for i,v in dict.items():
			if len(v)>1:
				mfs=cgi.MiniFieldStorage(i,v)
			else:
				mfs=cgi.MiniFieldStorage(i,v[0])				
			self.list.append(mfs)
			print "adding %s=%s" % (str(i),str(v))
			


		

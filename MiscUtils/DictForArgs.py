'''
DictForArgs.py


See the doc string for the DictForArgs() function.

Also, there is a test suite in Testing/TestDictForArgs.py
'''


import re, string


class DictForArgsError(Exception):
	pass

def _SyntaxError(s):
	raise DictForArgsError, 'Syntax error: %s' % repr(s)

def DictForArgs(s):
	'''
	Takes an input such as:
			x=3
			name="foo"
			first='john' last='doe'
			required border=3

	And returns a dictionary representing the same. For keys that aren't given an explicit value (such as 'required' above), the value is '1'.

	All values are interpreted as strings. If you want ints and floats, you'll have to convert them yourself.

	Returns {} for an empty string.

	The informal grammar is:
		(NAME [=NAME|STRING])*

	Will raise DictForArgsError if the string is invalid.
	'''

	s = string.strip(s)

	# Tokenize

	nameRE   = re.compile(r'\w+')
	equalsRE = re.compile(r'\=')
	stringRE = re.compile(r'''
					"[^"]+"|
					'[^']+'|
					\S+''', re.VERBOSE)
	whiteRE  = re.compile(r'\s+')
	REs = [nameRE, equalsRE, stringRE, whiteRE]

	verbose = 0
	matches = []
	start   = 0
	sLen    = len(s)

	if verbose:
		print '>> DictForArgs(%s)' % repr(s)
		print '>> sLen:', sLen
	while start<sLen:
		for regEx in REs:
			if verbose: print '>> try:', regEx
			match = regEx.match(s, start)
			if verbose: print '>> match:', match
			if match is not None:
				if match.re is not whiteRE:
					matches.append(match)
				start = match.end()
				if verbose: print '>> new start:', start
				break
		else:
			_SyntaxError(s)

	if verbose:
		names = []
		for match in matches:
			if match.re is nameRE:
				name = 'name'
			elif match.re is equalsRE:
				name = 'equals'
			elif match.re is stringRE:
				name = 'string'
			elif match.re is whiteRE:
				name = 'white'
			names.append(name)
			#print '>> match =', name, match
		print '>> names =', names


	# Process tokens

	# At this point we have a list of all the tokens (as re.Match objects)
	# We need to process these into a dictionary.

	dict = {}
	matchesLen = len(matches)
	i = 0
	while i<matchesLen:
		match = matches[i]
		if i+1<matchesLen:
			peekMatch = matches[i+1]
		else:
			peekMatch = None
		if match.re is nameRE:
			if peekMatch is not None:
				if peekMatch.re is nameRE:
					# We have a name without an explicit value
					dict[match.group()] = '1'
					i = i + 1
					continue
				if peekMatch.re is equalsRE:
					if i+2<matchesLen:
						target = matches[i+2]
						if target.re is nameRE  or  target.re is stringRE:
							value = target.group()
							if value[0]=="'" or value[0]=='"':
								value = value[1:-1]
								#value = "'''%s'''" % value[1:-1]
								#value = eval(value)
							dict[match.group()] = value
							i = i + 3
							continue
			else:
				dict[match.group()] = '1'
				i = i + 1
				continue
		_SyntaxError(s)


	if verbose:	print

	return dict

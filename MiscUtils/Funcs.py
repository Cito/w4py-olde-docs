'''
Funcs.py

Funcs.py, a member of MiscUtils, holds functions that don't fit in anywhere else.
'''

import string


def Commas(number):
	''' Returns the given number as a string with commas to separate the thousands positions. The number can be a float, int, long or string. Returns None for None. '''
	if number is None:
		return None
	if not number:
		return str(number)
	number = list(str(number))
	if '.' in number:
		i = number.index('.')
	else:
		i = len(number)
	while 1:
		i = i-3
		if i<=0:
			break
		number[i:i] = [',']
	return string.join(number, '')


def CharWrap(s, width, hanging=0):
	''' Returns a new version of the string word wrapped with the given width and hanging indent. The font is assumed to be monospaced.
	This can be useful for including text between <pre> </pre> tags since <pre> will not word wrap and for lengthly lines, will increase the width of a web page.
	It can also be used to help delineate the entries in log-style output by passing hanging=4.
	'''
	import string
	if not s:
		return s
	assert hanging<width
	hanging = ' ' * hanging
	lines = string.split(s, '\n')
	i = 0
	while i<len(lines):
		s = lines[i]
		while len(s)>width:
			t = s[width:]
			s = s[:width]
			lines[i] = s
			i = i + 1
			lines.insert(i, None)
			s = hanging + t
		else:
			lines[i] = s
		i = i + 1
	return string.join(lines, '\n')

"""
Funcs.py

Funcs.py, a member of MiscUtils, holds functions that don't fit in anywhere else.
"""

import md5, os, random, string, time


def commas(number):
	""" Returns the given number as a string with commas to separate the thousands positions. The number can be a float, int, long or string. Returns None for None. """
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


def charWrap(s, width, hanging=0):
	""" Returns a new version of the string word wrapped with the given width and hanging indent. The font is assumed to be monospaced.
	This can be useful for including text between <pre> </pre> tags since <pre> will not word wrap and for lengthly lines, will increase the width of a web page.
	It can also be used to help delineate the entries in log-style output by passing hanging=4.
	"""
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


def wordWrap(s, width=78):
	"""
	Returns a version of the string word wrapped to the given width.
	Respects existing newlines in the string.

	Taken from:
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
	"""
	return reduce(
		lambda line, word, width=width: "%s%s%s" % (
			line,
			' \n'[(len(line[line.rfind('\n')+1:]) + len(word) >= width)],
			word
		),
		s.split(' ')
	)


def dateForEmail(now=None):
	""" Returns a properly formatted date/time string for email messages """
	if now is None:
		now = time.localtime(time.time())
	if now[8]==1:
		offset = -time.altzone / 60
	else:
		offset = -time.timezone / 60
	if offset<0:
		plusminus = '-'
	else:
		plusminus = '+'
	return time.strftime('%a, %d %b %Y %H:%M:%S ', now) + plusminus + '%02d%02d' % (abs(offset/60), abs(offset%60))


def hostName():
	"""
	Returns the host name which is taken first from the os environment and failing that, from the 'hostname' executable. May return None if neither attempt succeeded.
	The environment keys checked are HOST and HOSTNAME both upper and lower case.
	"""
	for name in ['HOST', 'HOSTNAME', 'host', 'hostname']:
		hostName = os.environ.get(name, None)
		if hostName:
			break
	if not hostName:
		hostName = string.strip(os.popen('hostname').read())
	if not hostName:
		hostName = None
	else:
		hostName = string.lower(hostName)
	return hostName


def timestamp(numSecs=None):
	"""
	Returns a dictionary whose keys give different versions of the timestamp:
		'numSecs': the number of seconds
		'tuple': (year, month, day, hour, min, sec)
		'pretty': 'YYYY-MM-DD HH:MM:SS'
		'condensed': 'YYYYMMDDHHMMSS'
		'dashed': 'YYYY-MM-DD-HH-MM-SS'
	The focus is on the year, month, day, hour and second, with no additional information such as timezone or day of year. This form of timestamp is often ideal for print statements, logs and filenames.
	If the current number of seconds is not passed, then the current time is taken.
	The 'pretty' format is ideal for print statements, while the 'condensed' and 'dashed' formats are generally more appropriate for filenames.
	"""
	if numSecs is None:
		numSecs = time.time()
	tuple     = time.localtime(numSecs)[:6]
	pretty    = '%4i-%02i-%02i %02i:%02i:%02i' % tuple
	condensed = '%4i%02i%02i%02i%02i%02i' % tuple
	dashed    = '%4i-%02i-%02i-%02i-%02i-%02i' % tuple
	return locals()


def uniqueId(forObject=None):
	"""
	Generates an opaque, identifier string that is practically guaranteed to be unique.
	If an object is passed, then its id() is incorporated into the generation.
	Relies on md5 and returns a 32 character long string.
	"""
	r = [time.time(), random.random(), os.times()]
	if forObject is not None:
		r.append(id(forObject))
	md5object = md5.new(str(r))
	try:
		return md5object.hexdigest()
	except AttributeError:
		# Older versions of Python didn't have hexdigest, so we'll do it manually
		hexdigest = []
		for char in md5object.digest():
			hexdigest.append('%02x' % ord(char))
		return string.join(hexdigest, '')


### Deprecated

def Commas(number):
	print 'DEPRECATED: MiscUtils.Funcs.Commas() on 02/23/01 in ver 0.5. Use commas() instead.'
	return commas(number)

def CharWrap(s, width, hanging=0):
	print 'DEPRECATED: MiscUtils.Funcs.CharWrap() on 02/23/01 in ver 0.5. Use charWrap() instead.'
	return charWrap(s, width, hanging)

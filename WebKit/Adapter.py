from Configurable import Configurable


# @@ 2000-07-10 ce fix this up
import sys
try:
	import WebUtils
except ImportError:
	sys.path.append('..')
	import WebUtils
from WebUtils.WebFuncs import HTMLEncode

from Object import Object
from MiscUtils.Configurable import Configurable


class Adapter(Configurable, Object):

	def __init__(self):
		Configurable.__init__(self)
		Object.__init__(self)

	def name(self):
		return self.__class__.__name__

	def defaultConfig(self):
		return { }

	def configFilename(self):
		return 'Configs/%s.config' % self.name()


def WordWrap(s, width, hanging=0):
	''' Returns a new version of the string word wrapped with the given width and hanging indent. The font is assumed to be monospaced. This can be useful for including text between <pre> </pre> tags since <pre> will not word wrap and for lengthly lines, will increase the width of a web page. '''

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
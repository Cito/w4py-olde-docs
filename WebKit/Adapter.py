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

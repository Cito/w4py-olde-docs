'''
The Common module provides some commmon globals to all modules/classes in
WebKit. It's intended for internal use, not for modules outside the WebKit.

Typically usage is:

	from Common import *

The globals provided are:
	* the modules, os, string, sys and time
	* the root class, Object
	* the package WebUtils
	* the class SubclassResponsibilityError, an exception that methods in abstract classes often raise.
	* the class Tombstone when something unique and not-None is needed
'''


import os, string, sys, time

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

from Object import Object


try:
	import WebUtils
except:
	sys.path.append('..')  # because that's how the Webware tarball unravels
	import WebUtils


# @@ 2000-05-10 ce: Consider if all the following should be located in MiscUtils

class SubclassResponsibilityError(NotImplementedError):
	pass


def asclocaltime():
	''' Returns a readable string of the current, local time. Useful for time stamps in log files. '''
	return time.asctime(time.localtime(time.time()))


class Tombstone:
	''' Tombstone is used directly as a unique place holder object. It's an alternative to None when None can't be used (because it might be a valid value). This class is never instantiated. The Tombstone class itself, provides the identity needed. For example uses, search the source code. '''
	pass

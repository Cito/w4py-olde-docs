# MiscUtils package
# Webware for Python
# See ../README

__all__ = ['CSV', 'DataTable', 'NamedValueAccess']

__version__ = '0.4'


def InstallInWebKit(appServer):
	pass


# Beef up UserDict with the NamedValueAccess base class and custom versions of
# hasValueForKey() and valueForKey(). This all means that UserDict's (such as
# os.environ) are key/value accessible.
# @@ 2000-05-07 ce: This is duplicated from CGIWrapper.py.
from UserDict import UserDict
import NamedValueAccess
if not NamedValueAccess.NamedValueAccess in UserDict.__bases__:
	UserDict.__bases__ = UserDict.__bases__ + (NamedValueAccess.NamedValueAccess,)

	def _UserDict_hasValueForKey(self, key):
		return self.has_key(key)

	def _UserDict_valueForKey(self, key, default=None): # @@ 2000-05-10 ce: does Tombstone fit here and possibly in NamedValueAccess?
		return self.get(key, default)

	setattr(UserDict, 'hasValueForKey', _UserDict_hasValueForKey)
	setattr(UserDict, 'valueForKey', _UserDict_valueForKey)

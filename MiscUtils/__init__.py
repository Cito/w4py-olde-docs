# MiscUtils package
# Webware for Python
# See Documentation/MiscUtils.html

__all__ = ['Configurable', 'DBPool', 'DataTable', 'DictForArgs', 'Error', 'Funcs', 'MixIn', 'NamedValueAccess', 'PropertiesObject']


class NoDefault:
	'''
	This provides a singleton "thing" which can be used to initialize
	the "default=" arguments for different retrieval methods. For
	example:

		from MiscUtils import NoDefault
		def bar(self, name, default=NoDefault):
			if default is NoDefault:
				return self._bars[name]  # will raise exception for invalid key
			else:
				return self._bars.get(name, default)

	Consistently using a particular singleton is useful due to
	subclassing considerations:

		def bar(self, name, default=NoDefault):
			if someCondition:
				return self.specialBar(name)
			else:
				return SuperClass.bar(name, default)

	It's also useful if one method that uses "default=NoDefault" relies
	on another object and method to which it must pass the default.
	(This is similar to the subclassing situation.)
	'''
	pass


def InstallInWebKit(appServer):
	pass


# Beef up UserDict with the NamedValueAccess base class and custom versions of
# hasValueForKey() and valueForKey(). This all means that UserDict's (such as
# os.environ) are key/value accessible.
# @@ 2000-05-07 ce: CGIWrapper.py duplicates this.
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

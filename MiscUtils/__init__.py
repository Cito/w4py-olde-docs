# MiscUtils component
# Webware for Python
# See Docs/index.html

__all__ = ['Configurable', 'DBPool', 'DataTable', 'DictForArgs', 'Error', 'Funcs', 'MixIn', 'NamedValueAccess', 'PropertiesObject', 'unittest']


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

import string, sys
from types import DictType


class ConfigurationError(Exception):
	pass


class _NoDefault:
	pass


class Configurable:
	'''
	Configurable is an abstract superclass that provides configuration
	file functionality for subclasses.

	Subclasses should override:

		* defaultConfig()  to return a dictionary of default settings
		                   such as { 'Frequency': 5 }

		* configFilename() to return the filename by which users can
		                   override the configuration such as
		                   'Pinger.config'


	Subclasses typically use the setting() method, for example:

		time.sleep(self.setting('Frequency'))


	They might also use the printConfig() method, for example:

		self.printConfig()      # or
		self.printConfig(file)


	Users of your software can create a file with the same name as
	configFilename() and selectively override settings. The format of
	the file is a Python dictionary.

	Subclasses can also override userConfig() and get the user
	configuration settings from another source.
	'''

	## Init ##

	def __init__(self):
		self._config = None


	## Configuration

	def config(self):
		''' Returns the configuration of the object as a dictionary. This is a combination of defaultConfig() and userConfig(). This method caches the config. '''
		if self._config is None:
			self._config = self.defaultConfig()
			self._config.update(self.userConfig())
		return self._config

	def setting(self, name, default=_NoDefault):
		''' Returns the value of a particular setting in the configuration. '''
		if default is _NoDefault:
			return self.config()[name]
		else:
			return self.config().get(name, default)

	def hasSetting(self, name):
		return self.config().has_key(name)

	def defaultConfig(self):
		''' Returns a dictionary containing all the default values for the settings. This implementation returns {}. Subclasses should override. '''
		return {}

	def configFilename(self):
		''' Returns the filename by which users can override the configuration. Subclasses must override to specify a name. Returning None is valid, in which case no user config file will be loaded. '''
		raise SubclassResponsibilityError()

	def userConfig(self):
		''' Returns the user config overrides found in the optional config file, or {} if there is no such file. The config filename is taken from configFilename(). '''
		try:
			filename = self.configFilename()
			if filename is None:
				return {}
			file = open(filename)
		except IOError:
			return {}
		else:
			contents = file.read()
			file.close()
			try:
				config = eval(contents, {})
			except:
				raise ConfigurationError, 'Invalid configuration file, %s.' % self.configFilename()
			if type(config) is not DictType:
				raise ConfigurationError, 'Invalid type of configuration. Expecting dictionary, but got %s.'  % type(config)
			return config

	def printConfig(self, dest=None):
		''' Prints the configuration to the given destination, which defaults to stdout. A fixed with font is assumed for aligning the values to start at the same column. '''
		if dest is None:
			dest = sys.stdout
		keys = self.config().keys()
		keys.sort()
		width = max(map(lambda key: len(key), keys))
		for key in keys:
			dest.write(string.ljust(key, width)+' = '+str(self.setting(key))+'\n')
		dest.write('\n')

# KidKit
# Webware for Python

def InstallInWebKit(appServer):
	from WebKit.PlugIn import PlugInError
	try:
		try:
			from KidKit.Properties import requiredKidVersion
		except ImportError:
			raise PlugInError, 'Cannot determine required Kid version.'
		try:
			import kid
		except ImportError:
			raise PlugInError, \
				'Cannot import Kid. This needs to be installed to use KidKit.'
		try:
			kidVersion = tuple(map(lambda s:
					int('0' + ''.join(filter(lambda c: c.isdigit(), s))),
				kid.__version__.split('.', 3)[:3]))
		except ImportError:
			raise PlugInError, 'Cannot determine Kid version.'
		if kidVersion < requiredKidVersion:
			raise PlugInError, \
				'KidKit needs at least Kid version %s (installed is %s).' \
				% ('.'.join(map(str, requiredKidVersion)),
					'.'.join(map(str, kidVersion)))
		try:
			from KidServletFactory import KidServletFactory
			app = appServer.application()
			app.addServletFactory(KidServletFactory(app))
		except:
			from traceback import print_exc
			print_exc()
			raise PlugInError, 'Cannot install Kid servlet factory.'
	except PlugInError, e:
		print e
		print "KidKit will not be loaded."
		return

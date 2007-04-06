# MiddleKit

__version__ = '0.2'

__all__ = ['Core', 'Design', 'Run', 'StringTypes']

import os

try:
	from types import StringTypes
except ImportError: # fallback for Python < 2.2
	from types import StringType, UnicodeType
	StringTypes = (StringType, UnicodeType)

def InstallInWebKit(appServer):
	app = appServer.application()
	mkPathVia__file__ = os.path.join(os.getcwd(), os.path.dirname(__file__))
	#mkPathViaApp = app.serverSidePath(os.path.join(os.pardir, 'MiddleKit'))
	#assert mkPathVia__file__ == mkPathViaApp,
	#	'\nmkPathVia__file__=%r\nmkPathViaApp=%r\n' % (mkPathVia__file__, mkPathViaApp)
	path = os.path.join(mkPathVia__file__, 'WebBrowser')
	if os.path.exists(path):
		app.addContext('MKBrowser', path)
	else:
		print 'WARNING: Cannot locate %s.' % path

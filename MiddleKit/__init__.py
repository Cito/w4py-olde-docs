# MiddleKit

__version__ = '0.1'

__all__ = ['Core', 'Design', 'Run']

import os

def InstallInWebKit(appServer):
	app = appServer.application()
	mkPathVia__file__ = os.path.join(os.getcwd(), os.path.dirname(__file__))
	mkPathViaApp = app.serverSidePath(os.path.join(os.pardir, 'MiddleKit'))
	assert mkPathVia__file__==mkPathViaApp, '\nmkPathVia__file__=%r\nmkPathViaApp=%r\n' % (
		mkPathVia__file__, mkPathViaApp)
	path = os.path.join(mkPathViaApp, 'WebBrowser')
	if os.path.exists(path):
		app.addContext('MKBrowser', path)
	else:
		print 'WARNING: Cannot locate %s.' % path

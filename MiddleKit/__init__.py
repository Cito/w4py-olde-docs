# MiddleKit

__version__ = '0.1'

__all__ = ['Core', 'Design', 'Run']

import os

def InstallInWebKit(appServer):
	app = appServer.application()
	relPath = '../MiddleKit/WebBrowser'
	path = app.serverSidePath(relPath)
	if os.path.exists(path):
		app.addContext('MKBrowser', path)
	else:
		print 'WARNING: Cannot locate %s.' % relPath

# MiddleKit

__version__ = '0.1'

__all__ = ['Core', 'Design', 'Run']

import os

def InstallInWebKit(appServer):
	app = appServer.application()
	app.addContext('MKBrowser', os.path.normpath('../MiddleKit/WebBrowser'))

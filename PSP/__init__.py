# PSP
# Webware for Python

__version__ = 0.1


import os
from PSPServletFactory import PSPServletFactory

__version__='0.1'

def InstallInWebKit(appServer):
	app = appServer.application()
	app.addServletFactory(PSPServletFactory(app))
	app.setContext('PSPExamples', os.path.normpath('../PSP/Examples'))

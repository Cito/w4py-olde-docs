# PSP
# Webware for Python

__version__ = '0.3'


import os
from PSPServletFactory import PSPServletFactory


def InstallInWebKit(appServer):
	app = appServer.application()
	app.addServletFactory(PSPServletFactory(app))
	#app.setContext('PSPExamples', os.path.normpath('../PSP/Examples'))
	app.addContext('PSPExamples', os.path.normpath('../PSP/Examples'))

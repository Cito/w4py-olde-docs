# PSP
# Webware for Python

__version__ = 0.1


import os
from PSPServletFactory import PSPServletFactory


def InstallInWebKit(appServer):
	app = appServer.application()
	app.addServletFactory(PSPServletFactory(app))
	app._Contexts['PSPExamples']=os.path.normpath('../PSP/Examples')

# PSP
# Webware for Python

import os
from PSPServletFactory import PSPServletFactory


def InstallInWebKit(appServer):
	app = appServer.application()
	app.addServletFactory(PSPServletFactory(app))
	app.addContext('PSPExamples', os.path.normpath('../PSP/Examples'))

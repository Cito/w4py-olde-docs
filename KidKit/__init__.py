# Webware for Python

from KidServletFactory import KidServletFactory

def InstallInWebKit( appServer ):
	app = appServer.application()
	app.addServletFactory( KidServletFactory(app) )

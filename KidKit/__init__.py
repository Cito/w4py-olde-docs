# Webware for Python

def InstallInWebKit( appServer ):
	try:
		import kidx
	except:
		print '\tCould not import kid library.  Not loading KidKit.'
		return
	
	from KidServletFactory import KidServletFactory

	app = appServer.application()
	app.addServletFactory( KidServletFactory(app) )

def contextInitialize(app, ctxPath):
	import os, sys

	try:
		import MiddleKit
	except ImportError:
		sys.path.insert(1, os.path.normpath(os.path.join(ctxPath, os.pardir, os.pardir)))
		import MiddleKit

	if 0:
		sys.stdout.flush()
		print '>> MiddleKit:', MiddleKit
		print '>> getcwd:', os.getcwd()
		print '>> sys.path:'
		print '\n'.join(sys.path)

	# fix up HTTPResponse for our purposes
	# @@ gat: what is this hack?  I'm commenting it out because it breaks MKBrowser.
	# @@ I also can't fathom why it's in here.
	#def hasNonBlankValue(self, name):
	#	if self.hasValue(name):
	#		return self.value(name).strip()!=''
	#	else:
	#		return 0
	#from HTTPRequest import HTTPRequest
	#HTTPRequest.hasNonBlankValue = hasNonBlankValue

	# Apply the automatic mixins.
	import MixIns

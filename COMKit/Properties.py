name = 'COMKit'

version = (0, 1, 0)

docs = [
	{'name': "User's Guide", 'file': 'UsersGuide.html'},
]

status = 'alpha'

synopsis = '''COMKit allows COM objects to be used in the multi-threaded versions of WebKit.  Especially useful for data access using ActiveX Data Objects. Requires Windows and Python win32 extensions.'''

requiredPyVersion = (1, 5, 2)

requiredOpSys = 'nt'

requiredSoftware = [
	{'name': 'pythoncom'},
]

def willRunFunc():
	# WebKit doesn't check requiredSoftware yet.
	# So we do so:
	success = 0
	try:
		# For reasons described in the __init__.py, we can't actually import pythoncom
		# here, but we need to see if the module is available.  We can use the "imp"
		# standard module to accomplish this.
		import imp
		imp.find_module('pythoncom')
		success = 1
	except ImportError:
		pass
	if not success:
		return 'The pythoncom module is required to work with COM.'

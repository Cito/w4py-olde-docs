'''
FixPath.py
'''


def FixPathForMiddleKit():
	''' If MiddleKit can't be imported, this method will be invoked to augment the path.
	@@ 2001-02-02 ce: Should we always enhance the sys.path to make sure that the tests hit the MiddleKit they belong to and not some other MiddleKit?
	'''
	# We're located at .../MiddleKit/Run/Tests/Test.py.
	import os, sys
	if len(sys.path) and sys.path[0]=='':
		index = 1
	else:
		index = 0
	sys.path.insert(index, os.path.abspath('../..'))
	import MiddleKit

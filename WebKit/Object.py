import sys

try:
	import MiddleKit
except:
	sys.path.append('..')
	import WebUtils
from MiddleKit.KeyValueAccess import KeyValueAccess

class Object(KeyValueAccess):
	'''
	Object is the root class for all classes in the WebKit.
	
	This is a placeholder for any future functionality that might be appropriate
	for all objects in the framework.
	'''

	def __init__(self):
		''' Initializes the object. Subclasses should invoke super. '''
		pass

	# 2000-05-21 ce: Sometimes used for debugging:
	#
	#def __del__(self):
	#	print '>> del', self

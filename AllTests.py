#!/usr/bin/env python

'''
AllTests.py - This module runs the automated tests in all the components.

To run specific test cases, pass one or more names of package/module names 
on the command line which contain the test cases to be run.

Usage:
	python AllTests.py                  - Runs all the unittests
	python AllTests.py mypackage.MyFile - Runs the unittests in 'mypackage/MyFile'
	
This module also has a test-wide configuration file which can be accessed by
the function AllTests.config()
'''

import unittest, logging
import sys, os, site
from MiscUtils.Configurable import Configurable

_alltest_config = None

	
class _AllTestsConfig( Configurable ):
	'''
	Configuration for tests, e.g. which DBs to test, where to find DB utilities.
	
	If individual tests need some configuration, put it here so it is easy for
	a new user to configure all the tests in one place.
	'''
	
	def configFilename(self):
		return os.path.join( os.path.dirname(__file__), 'AllTests.config')
		
	def defaultConfig(self):
		default = {
			'mysql_test_info' : {
				'has_mysql'      : True,
				'mysql_client'   : '/usr/local/mysql/bin/mysql',
# 				'machine'        : 'localhost',
# 				'port'           : '3306',
 				'database'       : 'test',
# 				'user'           : 'test',
# 				'password'       : '',
				'extra_sys_path' : ['../../extern/MySQL-python-1.0.0/build/lib'],
			}	# mysql_test_info
		}
		return default


def config():
	'''
	Returns singleton of configuration file
	'''
	global _alltest_config
	if _alltest_config is None:
		_alltest_config = _AllTestsConfig()
		
	return _alltest_config
	


def checkAndAddPaths( listOfPaths ):
	'''
	Pass me a list of paths, and I will check that each one exists and add it 
	to sys.paths.  This is used by tests which need to use some required library such as
	database drivers.  
	'''
	numBadPaths = 0
	
	for p in listOfPaths:
		ap = os.path.abspath( p )
		if os.path.exists( ap ):
			site.addsitedir( ap )
		else:
			numBadPaths = numBadPaths + 1
			print 'WARNING: Could not find "%s".  Please edit "pythonPaths" in this script for your environment.' % ap
	
	return numBadPaths	# 0 = all were found
	
	
	
alltestnames = [
	'WebUtils.Tests.TestHTMLTag.makeTestSuite',
	
	'MiscUtils.Testing.TestCSVParser.CSVParserTests',
	'MiscUtils.Testing.TestNamedValueAccess.makeTestSuite',
	'MiscUtils.Testing.TestError.TestError',
	'MiscUtils.Testing.TestFuncs.TestFuncs',
	'MiscUtils.Testing.TestPickleCache.TestPickleCache',
	'MiscUtils.Testing.TestDataTable.TestDataTable',
	'MiscUtils.Testing.TestDictForArgs',

	'WebKit.Tests.Basic.Test',
	
	'TaskKit.Tests.Test.makeTestSuite',
	
	'PSP.Tests.PSPUtilsTest',
	'PSP.Tests.CompileTest',

	'UserKit.Tests.ExampleTest',
	'UserKit.Tests.Test',
	'UserKit.Tests.UserManagerTest.makeTestSuite',
]


if __name__ == '__main__':
	# Configure logging
	logging.basicConfig()	# default level is WARN
	
	# If no arguments are given, all of the test cases are run.
	if len(sys.argv) == 1:
		testnames = alltestnames
		verbosity = 2
		print '\n\nRunning All Webware Tests:'
	else:
		testnames = sys.argv[1:]
		# Turn up verbosity and logging level
		verbosity = 2
		logging.getLogger().setLevel( logging.DEBUG )
		print '\n\nRunning tests: %s\n' % testnames
	
	tests = unittest.TestSuite()
	
	# 	I could just use defaultTestLoader.loadTestsFromNames(), but it doesn't give a good
	#	error message when it cannot load a test.
	for t in testnames:
		try:
			tests.addTest( unittest.defaultTestLoader.loadTestsFromName(t) )
		except:
			print 'ERROR: Skipping tests from "%s".  I was trying to load it but got exception:' % t 
			sys.excepthook( *sys.exc_info() )
	
	unittest.TextTestRunner( verbosity=verbosity ).run(tests)

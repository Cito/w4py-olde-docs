#!/usr/bin/env python

'''
AllTests.py - This module runs the automated tests in all the components.

To run specific test cases, pass one or more names of package/module names 
on the command line which contain the test cases to be run.

Usage:
	python AllTests.py                  - Runs all the unittests
	python AllTests.py mypackage.MyFile - Runs the unittests in 'mypackage/MyFile'
'''

import unittest
import sys


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

# Many failures -- When somebody updates UserKit, they should fix these. [ww dec 04]
#	'UserKit.Tests.Test.makeTestSuite',
]


# If no arguments are given, all of the test cases are run.
if len(sys.argv) == 1:
	testnames = alltestnames
else:
	testnames = sys.argv[1:]
	print '\n\nRunning tests: %s\n' % testnames

tests = unittest.TestSuite()

# 	I could just use defaultTestLoader.loadTestsFromNames(), but it doesn't give a good
#	error message when it cannot load a test.
for t in testnames:
	try:
		tests.addTest( unittest.defaultTestLoader.loadTestsFromName(t) )
	except:
		print 'ERROR: Skipping tests from "%s" due to: %s' % (t, sys.exc_info()[1] )  

unittest.TextTestRunner(verbosity=1).run(tests)

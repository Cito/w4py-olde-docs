#!/usr/bin/env python

'''
AllTests.py - This module runs the automated tests in all the components.

To run specific test cases, pass one or more names of package/module names 
on the command line which contain the test cases to be run.

Usage:
	python AllTests.py                  - Runs all the unittests
	python AllTests.py mypackage.MyFile - Runs the unittests in 'mypackage/MyFile'
'''
#from MiscUtils import unittest
import unittest
import sys


suites = [
	'WebUtils.Tests.TestHTMLTag.makeTestSuite',
	
	'TaskKit.Tests.Test.makeTestSuite',

	'MiscUtils.Testing.TestCSVParser.CSVParserTests',
	'MiscUtils.Testing.TestNamedValueAccess.makeTestSuite',
	'MiscUtils.Testing.TestError.TestError',
	'MiscUtils.Testing.TestFuncs.TestFuncs',
	'PSP.Tests.PSPUtilsTest',
	'PSP.Tests.CompileTest',

# Many failures -- When somebody updates UserKit, they should fix these. [ww dec 04]
#	'UserKit.Tests.Test.makeTestSuite',
]


# If no arguments are given, all of the test cases are run.
if len(sys.argv) == 1:
	testnames = suites
else:
	testnames = sys.argv[1:]
	print '\n\nRunning tests: %s\n' % testnames

tests = unittest.defaultTestLoader.loadTestsFromNames(testnames)

unittest.TextTestRunner(verbosity=2).run(tests)

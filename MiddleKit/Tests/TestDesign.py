#!/usr/bin/env python
'''
TestDesign.py
'''

from TestCommon import *

from MiddleKit.Design.Generate import Generate
from MiddleKit.Core.Model import Model
import sys


def rmdir(dirname):
	''' Really remove the directory, even if it has files (and directories) in it. '''
	exceptions = (os.curdir, os.pardir)
	for name in os.listdir(dirname):
		if name not in exceptions:
			fullName = os.path.join(dirname, name)
			if os.path.isdir(fullName):
				rmdir(fullName)
			else:
				os.remove(fullName)
	os.rmdir(dirname)


def removeGenFiles(klasses):
	genFilenames = ['GeneratedPy', 'GeneratedSQL']
	genFilenames.extend([name+'.py' for name in klasses.keys()])
	genFilenames.extend([name+'.pyc' for name in klasses.keys()])
	stdout = sys.stdout
	first = 1
	for filename in genFilenames:
		if os.path.exists(filename):
			if first:
				stdout.write('Removing')
				first = 0
			stdout.write(' ' + filename)
			stdout.flush()
			if os.path.isdir(filename):
				rmdir(filename)
			else:
				os.remove(filename)
	if not first:
		sys.stdout.write('\n')
		stdout.flush()


def importPyClasses(klasses):
	# See if we can import all of the classes
	print 'importing classes:', ', '.join(klasses.keys())
	for klassName in klasses.keys():
		code = 'from %s import %s\n' % (klassName, klassName)
		#sys.stdout.write(code)
		results = {}
		exec code in results
		assert results.has_key(klassName)


def test(modelFilename):
	model = Model(modelFilename)
	klasses = model.klasses()
	removeGenFiles(klasses)
	Generate().main('Generate.py --db MySQL --model '+modelFilename)
	importPyClasses(klasses)
	return model


if __name__=='__main__':
	try:
		test(sys.argv[1])
	except:
		import traceback
		exc_info = sys.exc_info()
		traceback.print_exception(*exc_info)
		print '>> ABOUT TO EXIT WITH CODE 1'
		sys.exit(1)

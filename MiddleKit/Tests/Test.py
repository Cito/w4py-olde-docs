#!/usr/bin/env python
import time
startTime = time.time()

import os, sys
from TestCommon import *
from glob import glob


class RunError(Exception):
	"""
	Raised by Test.run() if the process exits with a non-zero status, which indicates an error.
	"""
	pass

class Test:

	## Init ##

	def __init__(self):
		pass


	## Customization ##

	def modelNames(self):
		return self._modelNames


	## Testing ##

	def main(self, args=sys.argv):
		# We explicitly list the tests rather than scanning for them (via glob) in order to perform them in a certain order (simplest to most complex)
		self.readArgs(args)
		results = []
		for self._modelName in self.modelNames():
			print '*** %s ***\n' % self._modelName
			if not self._modelName.endswith('.mkmodel'):
				self._modelName += '.mkmodel'
			didFail = 0
			try:
				if self.canRun():
					self.testDesign()
					self.testEmpty()
					self.insertSamples()
					self.testSamples()
					rmdir(workDir)
					print '\n'
				else:
					didFail = '       skipped'
			except RunError:
				didFail = '*** FAILED ***'
			results.append((self._modelName, didFail))

		# summarize the results of each test
		print 'RESULTS'
		print '-------'
		for name, outcome in results:
			if not outcome:
				outcome = '     succeeded'
			print outcome, name

		# print duration for curiosity's sake
		print
		duration = time.time() - startTime
		print '%.0f seconds' % (duration)

	def readArgs(self, args):
		if len(args)>1:
			self._modelNames = args[1:]
		else:
			self._modelNames = '''
				MKBasic MKNone MKString MKDateTime MKDefaultMinMax
				MKTypeValueChecking MKInheritance MKInheritanceAbstract
				MKList MKObjRef MKObjRefReuse MKDelete MKDeleteMark
				MKMultipleStores MKMultipleThreads
				MKModelInh1 MKModelInh2 MKModelInh3
				MKExcel
			'''.split()

	def canRun(self):
		path = os.path.join(self._modelName, 'CanRun.py')
		if os.path.exists(path):
			file = open(path)
			names = {}
			exec file in names
			assert names.has_key('CanRun'), 'expecting a CanRun() function'
			return names['CanRun']()
		else:
			return 1

	def testEmpty(self):
		"""
		Run all TestEmpty*.py files in the model, in alphabetical order by name.
		"""
		names = glob(os.path.join(self._modelName, 'TestEmpty*.py'))
		if names:
			names.sort()
			for name in names:
				self.createDatabase()
				self.testRun(os.path.basename(name), deleteData=0)
		else:
			self.createDatabase()

	def testSamples(self):
		self.testRun('TestSamples.py', deleteData=0)

	def testRun(self, pyFile, deleteData):
		if os.path.exists(os.path.join(self._modelName, pyFile)):
			print '%s:' % pyFile
			self.run('python TestRun.py %s %s delete=%i' % (self._modelName, pyFile, deleteData))
		else:
			print 'NO %s TO TEST.' % pyFile

	def testDesign(self):
		self.run('python TestDesign.py %s' % self._modelName)

	def createDatabase(self):
		filename = workDir + '/GeneratedSQL/Create.sql'
		filename = os.path.normpath(filename)
		cmd = '%s < %s' % (sqlCommand, filename)
		self.run(cmd)

	def insertSamples(self):
		self.createDatabase()
		filename = workDir + '/GeneratedSQL/InsertSamples.sql'
		filename = os.path.normpath(filename)
		if os.path.exists(filename):
			cmd = '%s < %s' % (sqlCommand, filename)
			self.run(cmd)


	## Self utility ##

	def run(self, cmd):
		"""
		Self utility method to run a system command. If the command
		has a non-zero exit status, raises RunError. Otherwise,
		returns 0.

		Note that on Windows ME, os.system() always returns 0 even if
		the program was a Python program that exited via sys.exit(1) or
		an uncaught exception. On Windows XP Pro SP 1, this problem
		does not occur. Windows ME has plenty of other problems as
		well; avoid it.
		"""
		print '<cmd>', cmd
		sys.stdout.flush()
		sys.stderr.flush()
		returnCode = os.system(cmd)
		sys.stdout.flush()
		sys.stderr.flush()

		if returnCode:
			raise RunError, returnCode

		#print '>> RETURN CODE =', returnCode
		return returnCode


if __name__=='__main__':
	Test().main()

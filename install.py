#!/usr/bin/env python

'''
install.py
Webware for Python

FUTURE
	* Look for an install.py in each component directory and run it
	  (there's not a strong need right now).
	* Upon successful install, create "installed" file with info such
	  as date, time, py ver, etc. Maybe just put the output of this
	  in there.
'''


import os, string, sys
from time import time, localtime, asctime
from string import strip, replace
from glob import glob

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO


class Installer:


	## Init ##

	def __init__(self):
		self._nameAndVer = strip(open('_VERSION').readlines()[0])
		self._comps = []  # components


	## Running the installation ##

	def run(self, verbose=0):
		self._verbose = verbose
		self.printHello()
		self.detectComponents()
		self.installDocs()
		self.fixPermissions()
		self.finished()
		self.printGoodbye()
		return self

	def printHello(self):
		print self._nameAndVer
		print 'Installer'
		print
		self.printKeyValue('Date', asctime(localtime(time())))
		self.printKeyValue('Python ver', sys.version)
		self.printKeyValue('Op Sys', os.name)
		self.printKeyValue('Platform', sys.platform)
		self.printKeyValue('Cur dir', os.getcwd())
		print

	def detectComponents(self):
		print 'Scanning for components...'
		for filename in os.listdir('.'):
			if os.path.isdir(filename):
				name = os.path.join(filename, 'Documentation')
				if os.path.isdir(name):
					self._comps.append(filename)
					print '  yes', filename
				else:
					print '   no', filename
		print

	def installDocs(self):
		self.propagateStyleSheet()
		self.createBrowsableSource()

	def propagateStyleSheet(self):
		''' Copy Documentation/StyleSheet.css into other Documentation dirs. '''
		print 'Propagating stylesheet...'
		stylesheet = open('Documentation/StyleSheet.css', 'rb').read()
		for comp in self._comps:
			print '  %s...' % comp
			target = os.path.join(comp, 'Documentation', 'StyleSheet.css')
			open(target, 'wb').write(stylesheet)
		print

	def createBrowsableSource(self):
		''' Create HTML documents for class hierarchies, summaries, source files, etc. '''

		print 'Creating browsable source...'
		self.requirePath('DocSupport')

		for comp in self._comps:
			print '  %s...' % comp

			sourceDir = '%s/Documentation/Source' % comp
			self.makeDir(sourceDir)

			filesDir = sourceDir + '/Files'
			self.makeDir(filesDir)

			summariesDir = sourceDir + '/Summaries'
			self.makeDir(summariesDir)

			docsDir = sourceDir + '/Docs'  # @@ 2000-08-17 ce: Eventually for pydoc/gendoc
			#self.makeDir(docsDir)

			for filename in glob('%s/*.py' % comp):
				self.createHighlightedSource(filename, filesDir)
				self.createSummary(filename, summariesDir)
				#self.createDocs(filename, docsDir)  # @@ 2000-08-17 ce: Eventually for pydoc/gendoc

			self.createBrowsableClassHier(comp, sourceDir)
			#self.createBrowsableFileList(comp, sourceDir)
		print

	def createHighlightedSource(self, filename, dir):
		import py2html
		targetName = '%s/%s.html' % (dir, os.path.basename(filename))
		if self._verbose: print '    Creating %s...' % targetName
		realout = sys.stdout
		sys.stdout = StringIO()
#		py2html.main([None, '-stdout', '-format:rawhtml', '-files', filename])
		py2html.main([None, '-stdout', '-files', filename])
		result = sys.stdout.getvalue()
		result = replace(result, '\t', '    ')  # 4 spaces per tab
		open(targetName, 'w').write(result)
		sys.stdout = realout

	def createSummary(self, filename, dir):
		from PySummary import PySummary
		targetName = '%s/%s.html' % (dir, os.path.basename(filename))
		if self._verbose: print '    Creating %s...' % targetName
		sum = PySummary()
		sum.readConfig('DocSupport/PySummary.config')
		sum.readFileNamed(filename)
		html = sum.html()
		open(targetName, 'w').write(html)

	def createDocs(self, filename, dir):
		from PySummary import PySummary
		targetName = '%s/%s.html' % (dir, os.path.basename(filename))
		if self._verbose: print '    Creating %s...' % targetName
		# @@ 2000-08-17 ce: use something like pydoc or gendoc here
		raise NotImplementedError

	def createBrowsableClassHier(self, filesDir, docsDir):
		''' Create HTML class hierarchy listings of the source files. '''
		from classhier import ClassHier

		classHierName = os.path.join(os.getcwd(), docsDir, 'ClassHier.html')
		listName = os.path.join(os.getcwd(), docsDir, 'ClassList.html')
		saveDir = os.getcwd()
		os.chdir(filesDir)
		try:
			ch = ClassHier()
			# @@ 2000-08-17 ce:  whoa! look at that hard-coding!
			ch.addFilesToIgnore(['zCookieEngine.py', 'WebKitSocketServer.py', '_on_hold_HierarchicalPage.py', 'fcgi.py'])
			ch.readFiles('*.py')
			ch.printHierForWeb(classHierName)
			ch.printListForWeb(listName)
		finally:
			os.chdir(saveDir)

	def createBrowsableFileList(self, filesDir, docsDir):
		''' Create HTML list of the source files. '''
		# @@ 2000-08-18 ce: not yet
		fullnames = glob('%s/*.py' % filesDir)
		filenames = map(lambda filename: os.path.basename(filename), fullnames)
		filenames.sort()
		ht = []
		ht.append('<table cellpadding=2 cellspacing=0 style="font-family: Arial, Helvetica, sans-serif; font-size: 14;">\n')
		for filename in filenames:
			ht.append('<tr> <td> summary </td> <td> source </td> <td> %s </td> </tr>' % filename)
		ht.append('</table>')
		ht = string.join(ht, '')
		open(docsDir+'/FileList.html', 'w').write(ht)

	def fixPermissions(self):
		if os.name=='posix':
			print 'Fixing permissions on CGI scripts...'
			for comp in self._comps:
				print '  %s...' % comp
				for filename in glob('%s/*.cgi' % comp):
					#if self._verbose: print '    %s...' % os.path.basename(filename)
					cmd = 'chmod a+rx %s' % filename
					print '    %s' % cmd
					os.system(cmd)
			print

	def finished(self):
		''' This method is invoked just before printGoodbye(). It is a hook for subclasses. This implementation does nothing. '''
		pass

	def printGoodbye(self):
		print '''
Installation looks successful.

Welcome to Webware!

You can find more information at:
  * Documentation/Webware.html  (e.g., local docs)
  * http://webware.sourceforge.net

Installation is finished.'''


	## Self utility ##

	def printKeyValue(self, key, value):
		print '%12s: %s' % (key, value)

	def makeDir(self, dirName):
		if not os.path.exists(dirName):
			if self._verbose: print '    Making %s...' % dirName
			os.mkdir(dirName)

	def requirePath(self, path):
		if path not in sys.path:
			sys.path.insert(1, path)


if __name__=='__main__':
	Installer().run(verbose=0)

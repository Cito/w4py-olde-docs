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
		print "initing"
		self._nameAndVer = strip(open('_VERSION').readlines()[0])
		self._comps = []  # components
		print "done initing"


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
		''' Create colorized, HTML versions of the source. '''
		print 'Creating browsable source...'
		sys.path.insert(0, 'DocSupport')
		import py2html

		for comp in self._comps:
			print '  %s...' % comp

			dirName = '%s/Documentation/Source' % comp
			if not os.path.exists(dirName):
				if self._verbose: print '    Making %s...' % dirName
				os.mkdir(dirName)

			for filename in glob('%s/*.py' % comp):
				targetName = '%s/Documentation/Source/%s.html' % (comp, os.path.basename(filename))
				if self._verbose: print '    Creating %s...' % targetName
				realout = sys.stdout
				sys.stdout = StringIO()
#				py2html.main([None, '-stdout', '-format:rawhtml', '-files', filename])
				py2html.main([None, '-stdout', '-files', filename])
				result = sys.stdout.getvalue()
				result = replace(result, '\t', '    ')  # 4 spaces per tab
				open(targetName, 'w').write(result)
				sys.stdout = realout
		print

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


if __name__=='__main__':
	Installer().run(verbose=0)

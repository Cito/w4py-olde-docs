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
from string import join, split, strip, replace
from glob import glob

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO


class Installer:
	'''
	The _comps attribute is a list of components, each of which is a dictionary initialized mostly from the component's Properties.py.
	'''

	## Init ##

	def __init__(self):
		self._nameAndVer = strip(open('_VERSION').readlines()[0])
		self._ver = split(self._nameAndVer)[1]
		self._comps = []
		self._htHeader = self.htFragment('Header')
		self._htFooter = self.htFragment('Footer')


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
				propName = os.path.join(filename, 'Properties.py')
				if os.path.exists(propName):
					comp = self.readProperties(propName)
					comp['filename'] = filename
					self._comps.append(comp)
					print '  yes', filename
				else:
					print '   no', filename
		print
		self._comps.sort(lambda a, b: cmp(a['name'], b['name']))

	def readProperties(self, filename):
		''' Returns a dictionary of values from executing the given Python properties file. '''
		results = {}
		contents = open(filename).read()
		if os.name=='posix':
			# get rid of CRs on posix, cuz Python's exec statement
			# will barf on them (even though a straight out script
			# works fine)
			contents = string.replace(contents, '\015', '')
		exec contents in results
		# get rid of stuff like '__builtins__'
		for key in results.keys():
#			if key.startswith('__'):
			if key[:2]=='__':
				del results[key]
		return results

	def installDocs(self):
		self.propagateStyleSheet()
		self.processRawFiles()
		self.createBrowsableSource()
		self.createComponentIndex()
		self.createIndex()
		self.createComponentIndexes()

	def propagateStyleSheet(self):
		''' Copy Documentation/StyleSheet.css into other Documentation dirs. '''
		print 'Propagating stylesheet...'
		stylesheet = open('Documentation/StyleSheet.css', 'rb').read()
		for comp in self._comps:
			#print '  %s...' % comp['filename']
			target = os.path.join(comp['filename'], 'Documentation', 'StyleSheet.css')
			open(target, 'wb').write(stylesheet)
		print

	def processRawFiles(self):
		print 'Processing raw files...'
		self.requirePath('DocSupport')
		from RawToHTML import RawToHTML
		processor = RawToHTML()
		processor.main(['install.RawToHTML', 'Documentation/*.raw'])
		print

	def createBrowsableSource(self):
		''' Create HTML documents for class hierarchies, summaries, source files, etc. '''

		print 'Creating browsable source...'
		self.requirePath('DocSupport')

		for comp in self._comps:
			filename = comp['filename']
			print '  %s...' % filename

			sourceDir = '%s/Documentation/Source' % filename
			self.makeDir(sourceDir)

			filesDir = sourceDir + '/Files'
			self.makeDir(filesDir)

			summariesDir = sourceDir + '/Summaries'
			self.makeDir(summariesDir)

			docsDir = sourceDir + '/Docs'  # @@ 2000-08-17 ce: Eventually for pydoc/gendoc
			#self.makeDir(docsDir)

			for pyFilename in glob('%s/*.py' % filename):
				self.createHighlightedSource(pyFilename, filesDir)
				self.createSummary(pyFilename, summariesDir)
				#self.createDocs(pyFilename, docsDir)  # @@ 2000-08-17 ce: Eventually for pydoc/gendoc

			self.createBrowsableClassHier(filename, sourceDir)
			#self.createBrowsableFileList(filename, sourceDir)
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

	def createComponentIndex(self):
		print 'Creating ComponentIndex.html...'
		ht = []
		wr = ht.append
		wr("Don't know where to start? Try <a href=../WebKit/Documentation/index.html>WebKit</a>. <p>")
		wr('<table align=center border=0 cellpadding=2 cellspacing=2 width=100%>')
		wr('<tr class=ComponentHeadings> <td nowrap>Component</td> <td>Status</td> <td nowrap>Py ver</td> <td>Summary</td> </tr>')
		row = 0
		for comp in self._comps:
			comp = comp.copy()
			comp['name'] = '<a href=../%(filename)s/Documentation/index.html>%(name)s</a>' % comp
			#comp['version'] = '.'.join([str(x) for x in comp['version']])
			comp['version'] = join(map(lambda x: str(x), comp['version']), '.')
			#comp['requiredPyVersion'] = '.'.join([str(x) for x in comp['requiredPyVersion']])
			comp['requiredPyVersion'] = join(map(lambda x: str(x), comp['requiredPyVersion']), '.')
			comp['row'] = row+1
			wr('''\
<tr valign=top class=ComponentRow%(row)i>
	<td class=NameVersionCell> <span class=Name>%(name)s</span><br><span class=Version>%(version)s</span> </td>
	<td> %(status)s </td>
	<td> %(requiredPyVersion)s </td>
	<td> %(synopsis)s </td>
</tr>''' % comp)
			row = (row+1)%2  # e.g., 1, 2, 1, 2, ...
		wr('</table>')
		ht = '\n'.join(ht)
		self.writeDocFile('Webware Component Index', 'Documentation/ComponentIndex.html', ht, extraHead='<link rel=stylesheet href=ComponentIndex.css type=text/css>')

	def createIndex(self):
		print 'Creating index.html...'
		version = self._ver
		ht = self.htFragment('index')
		ht = ht % locals()
		self.writeDocFile('Webware Documentation', 'Documentation/index.html', ht, extraHead='<link rel=stylesheet href=index.css type=text/css>')

		# @@ 2000-12-23 Uh, we sneak in Copyright.html here until
		# we have a more general mechanism for adding the header
		# and footer to various documents
		ht = self.htFragment('Copyright')
		self.writeDocFile('Webware Copyright et al', 'Documentation/Copyright.html', ht)


	def createComponentIndexes(self):
		print "Creating components' index.html..."
		indexFrag = self.htFragment('indexOfComponent')
		webwareVersion = self._ver
		link = '<a href=%s>%s</a> <br>\n'
		for comp in self._comps:
			comp = comp.copy()
#			comp['version'] = '.'.join([str(x) for x in comp['version']])
			comp['version'] = join(map(lambda x: str(x), comp['version']), '.')
#			comp['requiredPyVersion'] = '.'.join([str(x) for x in comp['requiredPyVersion']])
			comp['requiredPyVersion'] = join(map(lambda x: str(x), comp['requiredPyVersion']), '.')
			comp['webwareVersion'] = webwareVersion

			# Replace comp['docs'] with a readable HTML version of itself
			ht = []
			for doc in comp['docs']:
				ht.append(link % (doc['file'], doc['name']))
			ht = ''.join(ht)
			comp['docs'] = ht

			# Set up release notes
			ht = []
			releaseNotes = glob(os.path.join(comp['filename'], 'Documentation', 'RelNotes-*.html'))
			if releaseNotes:
#				releaseNotes = [{'filename': os.path.basename(filename)} for filename in releaseNotes]
				results = []
				for filename in releaseNotes:
					results.append({'filename': os.path.basename(filename)})
				releaseNotes = results

				for item in releaseNotes:
					filename = item['filename']
					item['name'] = filename[filename.rfind('-')+1:filename.rfind('.')]
				releaseNotes.sort(self.sortReleaseNotes)
				for item in releaseNotes:
					ht.append(link % (item['filename'], item['name']))
			else:
				ht.append('None\n')
			ht = ''.join(ht)
			comp['releaseNotes'] = ht

			# Write file
			title = comp['name'] + ' Documentation'
			filename = os.path.join(comp['filename'], 'Documentation', 'index.html')
			contents = indexFrag % comp
			cssLink = '<link rel=stylesheet href=../../Documentation/index.css type=text/css>'
			self.writeDocFile(title, filename, contents, extraHead=cssLink)

	def finished(self):
		''' This method is invoked just before printGoodbye(). It is a hook for subclasses. This implementation does nothing. '''
		pass

	def printGoodbye(self):
		print '''
Installation looks successful.

Welcome to Webware!

You can find more information at:
  * Documentation/index.html  (e.g., local docs)
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

	def sortReleaseNotes(self, a, b):
		''' Used by createComponentIndexes(). You pass this to list.sort(). '''
		# We append '.0' below so that values like 'x.y' and 'x.y.z'
		# compare the way we want them too (x.y.z is newer than x.y)
		a = a['name']
		if a.count('.')==1:
			a = a + '.0'
		b = b['name']
		if b.count('.')==1:
			b = b + '.0'
		return -cmp(a, b)

	def htFragment(self, name):
		''' Returns an HTML fragment with the given name. '''
		return open(os.path.join('Documentation', name+'.htmlf')).read()

	def writeDocFile(self, title, filename, contents, extraHead=''):
		values = locals()
		file = open(filename, 'w')
		file.write(self._htHeader % values)
		file.write(contents)
		file.write(self._htFooter % values)
		file.close()


if __name__=='__main__':
	Installer().run(verbose=0)

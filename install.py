#!/usr/bin/env python

"""
install.py
Webware for Python

FUTURE
	* Look for an install.py in each component directory and run it
	  (there's not a strong need right now).
	* Upon successful install, put meaningful info in the "_installed"
	  file, such as date, time, py ver, etc. Maybe just put the output
	  of this installation script in there.
"""


import os, sys, compileall
from time import time, localtime, asctime
from glob import glob
from MiscUtils.PropertiesObject import PropertiesObject

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO


class Installer:
	"""Install Webware.

	The _comps attribute is a list of components,
	each of which is an instance of MiscUtils.PropertiesObject.
	"""

	## Init ##

	def __init__(self):
		self._props = PropertiesObject('Properties.py')
		self._htHeader = self.htFragment('Header')
		self._htFooter = self.htFragment('Footer')
		self._comps = []

	## debug printing facility
	def _nop (self, msg): pass
	def _printMsg (self, msg): print msg


	## Running the installation ##

	def run(self, verbose=0, passprompt=1, defaultpass=''):
		self._verbose = verbose
		self.printMsg = verbose and self._printMsg or self._nop
		self.clearInstalledFile()
		self.printHello()
		if not self.checkPyVersion() or not self.checkThreading():
			return
		self.detectComponents()
		self.installDocs()
		self.backupConfigs()
		self.compileModules()
		self.fixPermissions()
		self.setupWebKitPassword(passprompt, defaultpass)
		self.finished()
		self.printGoodbye()
		return self

	def clearInstalledFile(self):
		"""
		Removes the _installed file which will get created at the very
		end of installation, provided there are no errors.
		"""
		if os.path.exists('_installed'):
			os.remove('_installed')

	def printHello(self):
		print '%(name)s %(versionString)s' % self._props
		print 'Installer'
		print
		self.printKeyValue('Date', asctime(localtime(time())))
		self.printKeyValue('Python Ver', sys.version)
		self.printKeyValue('Op Sys', os.name)
		self.printKeyValue('Platform', sys.platform)
		self.printKeyValue('Cur Dir', os.getcwd())
		print

	def checkPyVersion(self, minver=(2,0)):
		"""Check for minimum required Python version."""
		try:
			ver = sys.version_info[:len(minver)]
			version = '.'.join(map(str, ver))
			minversion = '.'.join(map(str, minver))
		except AttributeError: # Python < 2.0
			from string import split, join
			ver = tuple(map(int, split(split(sys.version, ' ', 1)[0], '.')[:len(minver)]))
			version = join(map(str, ver), '.')
			minversion = join(map(str, minver), '.')
		if ver < minver:
			print 'This Release of Webware requires Python %s.' % minversion
			print 'Your currently used version is Python %s.' % version
			print 'Please go to http://www.python.org for the latest version of Python.'
			if ver[0] <= 1: # require at least Python 2.0 for installation
				return 0 # otherwise stop here
			response = raw_input('\nYou may continue to install, '
				'but Webware may not perform as expected.\n'
				'Do you wish to continue with the installation?  [yes/no] ')
			return response[:1].upper() == "Y"
		return 1

	def checkThreading(self):
		try:
			import threading
		except ImportError:
			print '!!! Webware requires that Python be compiled with threading support.'
			print 'This version of Python does not appear to support threading.'
			response = raw_input('\nYou may continue, '
				'but you will have to run the AppServer with a Python\n'
				'interpreter that has threading enabled.'
				'Do you wish to continue with the installation? [yes/no] ')
			return response[:1].upper() == "Y"
		return 1

	def detectComponents(self):
		print 'Scanning for components...'
		dirnames = filter(os.path.isdir, os.listdir('.'))
		maxLen = max(map(len, dirnames))
		column = 0
		for dirname in dirnames:
			propName = os.path.join(dirname, 'Properties.py')
			print dirname.ljust(maxLen, '.'),
			if os.path.exists(propName):
				comp = PropertiesObject(propName)
				comp['dirname'] = dirname
				self._comps.append(comp)
				print 'yes',
			else:
				print 'no ',
			if column < 2:
				print '   ',
				column = column + 1
			else:
				print
				column = 0
		if column:
			print
		print
		self._comps.sort(lambda a, b: cmp(a['name'], b['name']))

	def setupWebKitPassword(self, prompt, defpass):
		"""Setup a password for WebKit Application server."""
		print 'Setting the WebKit password...'
		print
		if prompt:
			print 'Choose a password for the WebKit Application Server.'
			print 'If you will just press enter without entering anything,'
			if defpass is None:
				print 'a password will be automatically generated.'
			else:
				print 'the password specified on the command-line will be used.'
			import getpass
			password = getpass.getpass()
		else:
			if defpass is None:
				print 'A password will be automatically generated.'
			else:
				print 'A password was specified on the command-line.'
			password = None
		print 'You can check the password after installation at:'
		print 'WebKit/Configs/Application.config'
		if not password:
			if defpass is None:
				from string import letters, digits
				from random import choice
				password = ''.join(map(choice, [letters + digits]*8))
			else:
				password = defpass
		try: # read config file
			data = open('WebKit/Configs/Application.config', 'r').read()
		except IOError:
			print 'Error reading config file, possibly a permission problem,'
			print 'password not replaced, make sure to edit it by hand.'
			return
		# This will search for the construct "'AdminPassword': '...'"
		# and replace '...' with the content of the 'password' variable:
		if data.lstrip().startswith('{'):
			pattern = "('AdminPassword'\s*:)\s*'.*?'"
		else: # keyword arguments style
			pattern = "(AdminPassword\\s*=)\\s*['\"].*?['\"]"
		repl = "\g<1> '%s'" % (password,)
		from re import subn
		data, count = subn(pattern, repl, data)
		if count != 1:
			print "Warning:",
			if count > 1:
				print "More than one 'AdminPassword' in config file."
			else:
				print "'AdminPassword' not found in config file."
			return
		try: # write back config file
			open('WebKit/Configs/Application.config', 'w').write(data)
		except IOError:
			print 'Error writing config file, possibly a permission problem,'
			print 'password not replaced, make sure to edit it by hand.'
			return
		print 'Password replaced successfully.'

	def installDocs(self):
		self.propagateStyleSheet()
		self.processRawFiles()
		self.createBrowsableSource()
		self.createComponentIndex()
		self.createIndex()
		self.createComponentIndexes()

	def propagateStyleSheet(self):
		"""Copy stylesheets in / into the other Docs dirs."""
		print 'Propagating stylesheets...'
		for name in ['StyleSheet.css', 'GenIndex.css']:
			stylesheet = open('Docs/%s' % name, 'rb').read()
			for comp in self._comps:
				#print '  %s...' % comp['dirname']
				target = os.path.join(comp['dirname'], 'Docs', name)
				open(target, 'wb').write(stylesheet)
		print

	def processRawFiles(self):
		print 'Processing raw html doc files...'
		from DocSupport.RawToHTML import RawToHTML
		processor = RawToHTML()
		dirs = ['.'] + [comp['dirname'] for comp in self._comps]
		for dir in dirs:
			processor.main((None, dir + '/Docs/*.rawhtml'))
		print

	def createBrowsableSource(self):
		"""Create HTML documents for class hierarchies, summaries, source files, etc."""
		print 'Creating html source, summaries and doc files...'
		dirs = [comp['dirname'] for comp in self._comps]
		for dir in dirs:
			print '  %s...' % dir
			sourceDir = '%s/Docs/Source' % dir
			self.makeDir(sourceDir)
			filesDir = sourceDir + '/Files'
			self.makeDir(filesDir)
			summariesDir = sourceDir + '/Summaries'
			self.makeDir(summariesDir)
			docsDir = sourceDir + '/Docs'
			self.makeDir(docsDir)
			for pyFilename in glob('%s/*.py' % dir):
				self.createHighlightedSource(pyFilename, filesDir)
				self.createPySummary(pyFilename, summariesDir)
				self.createPyDocs(pyFilename, docsDir)
			self.createPyDocs(dir, docsDir)
			self.createFileList(dir, sourceDir)
			self.createClassList(dir, sourceDir)
		print

	def createHighlightedSource(self, filename, dir):
		"""Create highlighted HTML source code using py2html."""
		from DocSupport import py2html
		module = os.path.splitext(os.path.basename(filename))[0]
		targetName = '%s/%s.html' % (dir, module)
		self.printMsg('    Creating %s...' % targetName)
		stdout = sys.stdout
		sys.stdout = StringIO()
		py2html.main((None, '-stdout', '-files', filename))
		result = sys.stdout.getvalue()
		sys.stdout = stdout
		open(targetName, 'w').write(result)

	def createPySummary(self, filename, dir):
		"""Create a HTML module summary."""
		from DocSupport.PySummary import PySummary
		module = os.path.splitext(os.path.basename(filename))[0]
		targetName = '%s/%s.html' % (dir, module)
		self.printMsg('    Creating %s...' % targetName)
		sum = PySummary()
		sum.readConfig('DocSupport/PySummary.config')
		sum.readFileNamed(filename)
		html = sum.html()
		open(targetName, 'w').write(html)

	def createPyDocs(self, filename, dir):
		"""Create a HTML module documentation using pydoc."""
		try:
			import pydoc
		except ImportError:
			from MiscUtils import pydoc
		package, module = os.path.split(filename)
		module = os.path.splitext(module)[0]
		if package:
			module = package + '.' + module
		targetName = '%s/%s.html' % (dir, module)
		self.printMsg('    Creating %s...' % targetName)
		saveDir = os.getcwd()
		try:
			os.chdir(dir)
			targetName = '../' + targetName
			stdout = sys.stdout
			sys.stdout = StringIO()
			try:
				pydoc.writedoc(module)
			except:
				pass
			msg = sys.stdout.getvalue()
			sys.stdout = stdout
			if msg:
				self.printMsg(msg)
		finally:
			os.chdir(saveDir)

	def createFileList(self, filesDir, docsDir):
		"""Create a HTML list of the source files."""
		from DocSupport.FileList import FileList
		name = os.path.basename(filesDir)
		self.printMsg('    Creating file list of %s...' % name)
		filelist = FileList(name)
		saveDir = os.getcwd()
		os.chdir(filesDir)
		try:
			filelist.readFiles('*.py')
			targetName = '../' + docsDir + '/FileList.html'
			self.printMsg('    Creating %s...' % targetName)
			filelist.printForWeb(targetName)
		finally:
			os.chdir(saveDir)

	def createClassList(self, filesDir, docsDir):
		"""Create a HTML class hierarchy listing of the source files."""
		from DocSupport.ClassList import ClassList
		name = os.path.basename(filesDir)
		self.printMsg('    Creating class list of %s...' % name)
		classlist = ClassList(name)
		saveDir = os.getcwd()
		os.chdir(filesDir)
		try:
			classlist.readFiles('*.py')
			targetName = '../' + docsDir + '/ClassList.html'
			self.printMsg('    Creating %s...' % targetName)
			classlist.printForWeb(0, targetName)
			targetName = '../' + docsDir + '/ClassHierarchy.html'
			self.printMsg('    Creating %s...' % targetName)
			classlist.printForWeb(1, targetName)
		finally:
			os.chdir(saveDir)

	def createComponentIndex(self):
		"""Create a HTML component index of Webware itself."""
		print 'Creating ComponentIndex.html...'
		ht = []
		wr = ht.append
		wr('<p>Don\'t know where to start? '
			'Try <a href="../WebKit/Docs/index.html">WebKit</a>.</p>')
		wr('<table align="center" border="0" '
			'cellpadding="2" cellspacing="2" width="100%">')
		wr('<tr class="ComponentHeadings">'
			'<th>Component</th><th>Status</th><th>Ver</th>'
			'<th>Py</th><th>Summary</th></tr>')
		row = 0
		for comp in self._comps:
			comp['nameAsLink'] = ('<a href='
				'"../%(dirname)s/Docs/index.html">%(name)s</a>' % comp)
			comp['indexRow'] = row + 1
			wr('<tr valign="top" class="ComponentRow%(indexRow)i">'
				'<td class="NameVersionCell">'
				'<span class="Name">%(nameAsLink)s</span></td>'
				'<td>%(status)s</td>'
				'<td><span class="Version">%(versionString)s</span></td>'
				'<td>%(requiredPyVersionString)s</td>'
				'<td>%(synopsis)s</td></tr>' % comp)
			row = 1 - row
		wr('</table>')
		ht = '\n'.join(ht)
		self.writeDocFile('Webware Component Index',
			'Docs/ComponentIndex.html', ht,
			extraHead='<link rel="stylesheet" '
			'href="ComponentIndex.css" type="text/css">')

	def createIndex(self):
		"""Create start page for Webware docs from fragment."""
		print 'Creating index.html...'
		ht = self.htFragment('index')
		ht = ht % self._props
		self.writeDocFile('Webware Documentation',
			'Docs/index.html', ht,
			extraHead='<link rel="stylesheet" '
			'href="GenIndex.css" type="text/css">')
		# @@ 2000-12-23 Uh, we sneak in Copyright.html here until we have a
		# more general mechanism for adding header/footer to various documents
		ht = self.htFragment('Copyright')
		self.writeDocFile('Webware Copyright et al',
			'Docs/Copyright.html', ht)
		# @@ 2001-03-11 ce: Uh, we sneak in RelNotes.html here, as well
		ht = self.htFragment('RelNotes')
		self.writeDocFile('Webware Release Notes',
			'Docs/RelNotes.html', ht)

	def createComponentIndexes(self):
		"""Create start page for all components."""
		print "Creating index.html for all components..."
		indexFrag = self.htFragment('indexOfComponent')
		link = '<p><a href="%s">%s</a></p>'
		for comp in self._comps:
			comp['webwareVersion'] = self._props['version']
			comp['webwareVersionString'] = self._props['versionString']
			# Create 'htDocs' as a HTML fragment corresponding to comp['docs']
			ht = []
			for doc in comp['docs']:
				ht.append(link % (doc['file'], doc['name']))
			ht = ''.join(ht)
			comp['htDocs'] = ht
			# Set up release notes
			ht = []
			releaseNotes = glob(os.path.join(comp['dirname'],
				'Docs', 'RelNotes-*.html'))
			if releaseNotes:
				releaseNotes = [{'dirname': os.path.basename(filename)}
					for filename in releaseNotes]
				for item in releaseNotes:
					filename = item['dirname']
					item['name'] = filename[filename.rfind('-')+1:filename.rfind('.')]
					try:
						item['ver'] = map(int, item['name'].split('.'))
					except ValueError:
						item['ver'] = None
				releaseNotes.sort(lambda a, b: cmp(a['ver'], b['ver']))
				for item in releaseNotes:
					ht.append(link % (item['dirname'], item['name']))
			else:
				ht.append('<p>None</p>')
			ht = '\n'.join(ht)
			comp['htReleaseNotes'] = ht
			# Write file
			title = comp['name'] + ' Documentation'
			filename = os.path.join(comp['dirname'], 'Docs', 'index.html')
			ht = indexFrag % comp
			self.writeDocFile(title, filename, ht,
				extraHead='<link rel="stylesheet" '
				'href="GenIndex.css" type="text/css">')

	def backupConfigs(self):
		"""Copy *.config to *.config.default, if the .default files don't already exist.

		This allows the user to always go back to the default config file if needed
		(for troubleshooting for example).
		"""
		print 'Backing up original config files...'
		print '   ',
		self._backupConfigs(os.curdir)
		print

	def _backupConfigs(self, dir):
		wr = sys.stdout.write
		for filename in os.listdir(dir):
			fullPath = os.path.join(dir, filename)
			if os.path.isdir(fullPath):
				self._backupConfigs(fullPath)
			elif (filename[0]!='.' and \
				os.path.splitext(filename)[1] == '.config'):
				backupName = fullPath + '.default'
				if not os.path.exists(backupName):
					contents = open(fullPath, 'rb').read()
					open(backupName, 'wb').write(contents)
					del contents
					wr('.')
				else:
					wr('-')
				sys.stdout.flush()

	def compileModules(self):
		import StringIO
		print """Byte compiling all modules\n------------------------------------------\n"""
		stdout = sys.stdout
		stderr = sys.stderr
		sys.stdout = StringIO.StringIO() #the compileall is a little verbose
		sys.stderr = StringIO.StringIO()
		compileall.compile_dir(".", 10, '', 1)
		sys.stdout = stdout
		sys.stderr = stderr
		print "\n\n"

	def fixPermissions(self):
		if os.name=='posix':
			print 'Setting permissions on CGI scripts...'
			for comp in self._comps:
				#print '  %s...' % comp['name']
				for filename in glob('%s/*.cgi' % comp['dirname']):
					#self.printMsg('    %s...' % os.path.basename(filename))
					cmd = 'chmod a+rx %s' % filename
					print '  %s' % cmd
					os.system(cmd)
			print

	def finished(self):
		"""Finish the installation.

		This method is invoked just before printGoodbye().
		It writes the _installed file to disk.
		"""
		open('_installed', 'w').write('This file is written upon successful installation.\n'
			'Leave this file in place.\n')

	def printGoodbye(self):
		print '''
Installation looks successful.

Welcome to Webware!

You can find more information at:
  * Docs/index.html  (e.g., local docs)
  * http://www.webwareforpython.org

Installation is finished.'''


	## Self utility ##

	def printKeyValue(self, key, value):
		print '%12s: %s' % (key, value)

	def makeDir(self, dirName):
		if not os.path.exists(dirName):
			self.printMsg('    Making %s...' % dirName)
			os.mkdir(dirName)

	def htFragment(self, name):
		"""Return HTML fragment with the given name."""
		return open(os.path.join('Docs', name+'.htmlf')).read()

	def writeDocFile(self, title, filename, contents, extraHead=''):
		values = locals()
		file = open(filename, 'w')
		file.write(self._htHeader % values)
		file.write(contents)
		file.write(self._htFooter % values)
		file.close()


def printHelp():
	print 'Usage: install.py [options]'
	print 'Install WebWare in the local directory.'
	print
	print '  -h, --help                 Print this help screen.'
	print '  -v, --verbose              Print extra information messages during install.'
	print '  --password-prompt=no       Do not prompt for the WebKit password during install.'
	print '  --set-password=...         Set the WebKit password to the given value.'

if __name__=='__main__':
	import getopt
	verbose = 0
	passprompt = defaultpass = None
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "verbose", "password-prompt=", "set-password="])
	except getopt.GetoptError:
		printHelp()
	else:
		for o, a in opts:
			if o in ("-v", "--verbose"): verbose=1
			if o in ("--password-prompt",):
				if a in ("1", "yes", "true"):
					passprompt = 1
				elif a in ("0", "no", "false"):
					passprompt = 0
			if o in ("--set-password",):
				defaultpass = a
			if o in ("-h", "--help", "h", "help"):
				printHelp()
				sys.exit(0)
		if passprompt is None and defaultpass is None:
			passprompt = 1

		Installer().run(verbose=verbose, passprompt=passprompt, defaultpass=defaultpass)

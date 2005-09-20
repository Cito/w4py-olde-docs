#!/usr/bin/env python
#----------------------------------------------------------------------
#
# A script to build a WebKit work directory outside of the WebWare tree
#
# By Robin Dunn
#
#----------------------------------------------------------------------

"""\
MakeAppWorkDir.py

INTRODUCTION

This utility builds a directory tree that can be used as the current
working directory of an instance of the WebKit application server.  By
using a separate directory tree like this your application can run
without needing write access, etc. to the WebWare directory tree, and
you can also run more than one application server at once using the
same WebWare code.  This makes it easy to reuse and keep WebWare
updated without disturbing your applications.


COMMAND LINE USAGE

python MakeAppWorkDir.py [OPTIONS] SomeDir

OPTIONS:
-c SampleContextName  "SampleContextName" will be used for the pre-
                      installed context.  (Default "MyContext")
-d SampleContextDir   The directory where the context will be located
                      (so you can place the context outside of the workdir).
--cvsignore           .cvsignore files will be added
-l Dir                You may specify this option multiple times; all
   or --library Dir   directories you give will be added to sys.path.
"""

import sys, os, stat
import glob, shutil


class MakeAppWorkDir:
	"""Make a new application runtime directory for Webware.

	This class breaks down the steps needed to create a new runtime
	directory for webware.  That includes all the needed
	subdirectories, default configuration files, and startup scripts.
	Each step can be overridden in a derived class if needed.
	"""

	def __init__(self, webwareDir, workDir, verbose=1,
			sampleContext="MyContext",
			contextDir='',
			osType=None,
			addCVSIgnore=0,
			libraryDirs=None):
		"""Initializer for MakeAppWorkDir.  Pass in at least the
		Webware directory and the target working directory.  If you
		pass None for sampleContext then the default context will the
		the WebKit/Examples directory as usual.
		"""
		self._webwareDir = webWareDir
		self._webKitDir = os.path.join(webwareDir, "WebKit")
		self._workDir = os.path.abspath(workDir)
		self._verbose = verbose
		self._sampleContext = sampleContext
		self.contextDir = contextDir
		if osType is None:
			osType = os.name
		self._osType = osType
		self._addCVSIgnore = addCVSIgnore
		self._libraryDirs = libraryDirs

	def buildWorkDir(self):
		"""These are all the (overridable) steps needed to make a new runtime directory."""
		self.msg("Making a new runtime directory...")
		self.msg()
		self.makeDirectories()
		self.copyConfigFiles()
		self.copyOtherFiles()
		self.adjustLauncherScripts()
		if self._sampleContext is not None:
			self.makeDefaultContext()
		if self._addCVSIgnore:
			self.addCVSIgnore()
		self.printCompleted()

	def makeDirectories(self):
		"""Create all the needed directories if they don't already exist."""
		self.msg("Creating directory tree at %s" % self._workDir)
		standardDirs = (
			'', 'Cache', 'Configs', 'ErrorMsgs', 'Logs', 'Sessions')
		for dir in standardDirs:
			dir = os.path.join(self._workDir, dir)
			if os.path.exists(dir):
				self.msg("\t%s already exists." % dir)
			else:
				os.mkdir(dir)
				self.msg("\t%s created." % dir)
		for dir in self._libraryDirs:
			dir = os.path.join(self._workDir, dir)
			if not os.path.exists(dir):
				os.makedirs(dir)
				open(os.path.join(dir, '__init__.py'), 'w').write('#\n')
				self.msg("\t%s created." % dir)
		self.msg()

	def copyConfigFiles(self):
		"""Make a copy of the config files in the Configs directory."""
		self.msg("Copying config files...")
		configs = glob.glob(os.path.join(self._webKitDir, "Configs", "*.config"))
		for name in configs:
			newname = os.path.join(self._workDir, "Configs", os.path.basename(name))
			self.msg("\t%s" % newname)
			shutil.copyfile(name, newname)
			mode = os.stat(newname)[stat.ST_MODE]
			# remove public read/write/exec perms
			os.chmod(newname, mode & 0770)
		self.msg()

	def copyOtherFiles(self):
		"""Make a copy of any other necessary files in the new work dir."""
		self.msg("Copying other files...")
		otherFiles = (
			# (file, executable, platform, relocate)
			('404Text.txt', None, 0),
			('AppServer', 'posix', 1),
			('AppServer.bat', 'nt', 1),
			('Launch.py', None, 1),
			('AppServerService.py', 'nt', 1),
			('Adapters/WebKit.cgi', None, 1))
		for name, osType, doChmod in otherFiles:
			if osType and osType != self._osType:
				continue
			oldname = os.path.join(self._webKitDir, name)
			newname = os.path.join(self._workDir, os.path.basename(name))
			self.msg("\t%s" % newname)
			# Copy the file, adjusting the shebang magic
			firstLine = open(oldname).readline()
			if doChmod and firstLine.startswith('#!') \
					and firstLine.rstrip().endswith('python'):
				f = open(oldname)
				f.readline() # throw away the first line
				new = open(newname, 'w')
				new.write('#!%s\n' % sys.executable)
				new.write(f.read())
				new.close()
				f.close()
			else:
				shutil.copyfile(oldname, newname)
			if doChmod:
				os.chmod(newname, 0755)
		self.msg()

	def adjustLauncherScripts(self):
		"""Adjust the launcher scripts and the CGI adapter script."""
		self.msg("Adjusting the launcher scripts...")
		launchScripts = ('Launch.py', 'AppServerService.py', 'WebKit.cgi')
		substitutions = (
			('workDir', None, self._workDir),
			('webwareDir', None, self._webwareDir),
			('libraryDirs', [], self._libraryDirs))
		for name in launchScripts:
			filename = os.path.join(self._workDir, os.path.basename(name))
			if not os.path.exists(filename):
				continue
			self.msg("\t%s" % filename)
			script = open(filename, 'r').read()
			for s in substitutions:
				if name == 'WebKit.cgi':
					if s[0] == 'libraryDirs':
						continue
				else:
					if s[0] == 'workDir':
						continue
				pattern = '\n%s = %r\n' % s[:2]
				try:
					i = script.index(pattern)
				except:
					self.msg("\t%s cannot be set in %s." % (s[0], name))
				else:
					repl = '\n%s = %r\n' % (s[0], s[2])
					script = script[:i] + repl + script[i + len(pattern):]
			open(filename, 'w').write(script)
		self.msg()

	def makeDefaultContext(self):
		"""Make a very simple context for the newbie user to play with."""
		self.msg("Creating default context...")
		contextDir = os.path.join(
			self._workDir,
			self.contextDir or self._sampleContext)
		if contextDir.startswith(self._workDir):
			configDir = contextDir[len(self._workDir):]
			configDir = configDir.lstrip(os.sep)
			if os.altsep:
				configDir =  configDir.lstrip(os.altsep)
		else:
			configDir = contextDir
		if not os.path.exists(contextDir):
			os.makedirs(contextDir)
		for name in exampleContext:
			filename = os.path.join(contextDir, name)
			if not os.path.exists(filename):
				self.msg("\t%s" % filename)
				open(filename, "w").write(exampleContext[name])
		self.msg("Updating config for default context...")
		filename = os.path.join(self._workDir, "Configs", 'Application.config')
		self.msg("\t%s" % filename)
		content = open(filename).readlines()
		output  = open(filename, 'w')
		for line in content:
			if line.startswith("Contexts['default'] = "):
				output.write("Contexts[%r] = %r\n" % (self._sampleContext, configDir))
				output.write("Contexts['default'] = %r\n" % self._sampleContext)
			else:
				output.write(line)
		self.msg()

	def addCVSIgnore(self):
		self.msg("Creating .cvsignore files...")
		files = {'.': '*.pyc\naddress.*\nhttpd.*\nappserverpid.*',
			 'Cache': '[a-zA-Z0-9]*',
			 'ErrorMsgs': '[a-zA-Z0-9]*',
			 'Logs': '[a-zA-Z0-9]*',
			 'Sessions': '[a-zA-Z0-9]*',
			 self._sampleContext: '*.pyc\n*.pyo',
			 }
		for dir, contents in files.items():
			filename = os.path.join(self._workDir, dir, '.cvsignore')
			f = open(filename, 'w')
			f.write(contents)
			f.close()

	def printCompleted(self):
		run = os.path.abspath(os.path.join(self._workDir, 'AppServer'))
		print """
Congratulations, you've just created a runtime working directory for Webware.

To start the app server you can run this command:

    %s

By default the built-in HTTP server is activated. So you can immediately see
an example that has been generated for you to play with and to build upon by
pointing your browser to:

    http://localhost:8080

In a productive environment, you will probably want to use Apache or another
web server instead of the built-in HTTP server. The most somple (but least
performant) solution to do this is by using the Python WebKit.cgi CGI script.
Copy it to your web server's cgi-bin directory or anywhere else that it will
execute CGIs from. If you see import errors, you may need to modify the file
permissions on your Webware directory so that the CGI script can access it.

Have fun!
""" % run

	def msg(self, text=None):
		if self._verbose:
			if text:
				print text
			else:
				print

exampleContext = { # files copied to example context

# This is used to create a very simple sample context for the new
# work dir to give the newbie something easy to play with.

'__init.py__': """
def contextInitialize(appServer, path):
	# You could put initialization code here to be executed when
	# the context is loaded into WebKit.
	pass
""",

'Main.py': """
from WebKit.Page import Page

class Main(Page):

	def title(self):
		return 'My Sample Context'

	def writeContent(self):
		self.writeln('<h1>Welcome to Webware!</h1>')
		self.writeln('''
		This is a sample context generated for you and has purposly been kept very simple
		to give you something to play with to get yourself started.  The code that implements
		this page is located in <b>%s</b>.
		''' % self.request().serverSidePath())

		self.writeln('''
		<p>
		There are more examples and documentaion in the Webware distribution, which you
		can get to from here:<p><ul>
		''')

		adapterName = self.request().adapterName()
		ctxs = self.application().contexts().keys()
		ctxs = filter(lambda ctx: ctx!='default', ctxs)
		ctxs.sort()
		for ctx in ctxs:
			self.writeln('<li><a href="%s/%s/">%s</a>' % (adapterName, ctx, ctx))

		self.writeln('</ul>')
"""

} # end of example context files

if __name__ == "__main__":
	targetDir = None
	contextName = None
	contextDir = ''
	addCVSIgnore = 0
	libraryDirs = []
	args = sys.argv[1:]
	# lame little command-line handler
	while args:
		if args[0] == '--cvsignore':
			addCVSIgnore = 1
			args = args[1:]
			continue
		if args[0] == '-c':
			if len(args) < 2 or args[1].startswith('-'):
				print "Bad option: %s" % args[0]
				print __doc__
				sys.exit(2)
			contextName = args[1]
			args = args[2:]
			continue
		if args[0] == '-d':
			if len(args) < 2 or args[1].startswith('-'):
				print "Bad option: %s" % args[0]
				print __doc__
				sys.exit(2)
			contextDir = args[1]
			args = args[2:]
			continue
		if args[0] in ['-l', '--library']:
			if len(args) < 2 or args[1].startswith('-'):
				print "Bad option: %s" % args[0]
				print __doc__
				sys.exit(2)
			libraryDirs.append(args[1])
			args = args[2:]
			continue
		if not targetDir and not args[0].startswith('-'):
			targetDir = args[0]
			args = args[1:]
			continue
		# Must be an error:
		print "Unknown option: %s" % args[0]
		print __doc__
		sys.exit(1)
	if not targetDir:
		print "Give a target directory"
		print __doc__
		sys.exit(1)

	if contextDir and contextName is None:
		contextName = os.path.basename(contextDir)
	elif contextName is None:
		contextName = 'MyContext'

	# this assumes that this script is still located in Webware/bin
	p = os.path
	webWareDir = p.abspath(p.join(p.dirname(sys.argv[0]), ".."))

	mawd = MakeAppWorkDir(webWareDir, targetDir,
		sampleContext=contextName,
		contextDir=contextDir,
		addCVSIgnore=addCVSIgnore,
		libraryDirs=libraryDirs)
	mawd.buildWorkDir()


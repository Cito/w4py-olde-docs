#!/usr/bin/env python
#----------------------------------------------------------------------
#
# A script to build a WebKit work directory outside of the WebWare tree
#
# By Robin Dunn
#
#----------------------------------------------------------------------

"""
MakeAppWorkDir.py


INTRODUCTION

This utility builds a directory tree that can be used as the current
working directory of an instance of the WebKit applicaiton server.  By
using a separate directory tree like this your applicaion can run
without needing write access, etc. to the WebWare directory tree, and
you can also run more than one application server at once using the
same WebWare code.  This makes it easy to reuse and keep WebWare
updated without disturbing your applicaitons.


COMMAND LINE USAGE

	python MakeAppWorkDir.py SomeDir

"""

#----------------------------------------------------------------------

import sys, os, string
import glob, shutil

#----------------------------------------------------------------------

class MakeAppWorkDir:
	"""Make a new application runtime directory for Webware.

	This class breaks down the steps needed to create a new runtime
	directory for webware.  That includes all the needed
	subdirectories, default configuration files, and startup scripts.
	Each step can be overridden in a derived class if needed.
	"""

	def __init__(self, webWareDir, workDir, verbose=1, sampleContext="MyContext"):
		"""Initializer for MakeAppWorkDir.  Pass in at least the
		Webware directory and the target working directory.  If you
		pass None for sampleContext then the default context will the
		the WebKit/Examples directory as usual.
		"""
		self._webWareDir = webWareDir
		self._webKitDir = os.path.join(webWareDir, "WebKit")
		self._workDir = os.path.abspath(workDir)
		self._verbose = verbose
		self._substVals = {
		    "WEBWARE": string.replace(self._webWareDir, '\\', '/'),
		    "WEBKIT":  string.replace(self._webKitDir,	'\\', '/'),
		    "WORKDIR": string.replace(self._workDir,	'\\', '/'),
		    "DEFAULT": "%s/Examples" % string.replace(self._webKitDir,	'\\', '/'),
		    "DEFCTX":  "",
		    }
		self._sample = sampleContext
		if sampleContext is not None:
			self._substVals["DEFAULT"] = sampleContext
			self._substVals["DEFCTX"] =  "'%s':    '%s'," % (sampleContext, sampleContext)



	def buildWorkDir(self):
		"""These are all the (overridable) steps needed to make a new runtime direcotry."""
		self.makeDirectories()
		self.makeConfigFiles()
		self.makeLauncherScripts()
		self.copyOtherFiles()
		self.makeDefaultContext()
		self.printCompleted()



	def makeDirectories(self):
		"""Creates all the needed directories if they don't already exist."""
		self.msg("Creating directory tree at %s" % self._workDir)

		theDirs = [ self._workDir,
			    os.path.join(self._workDir, "Cache"),
			    os.path.join(self._workDir, "Cans"),  # TODO: should this one be here?
			    os.path.join(self._workDir, "Configs"),
			    os.path.join(self._workDir, "ErrorMsgs"),
			    os.path.join(self._workDir, "Logs"),
			    os.path.join(self._workDir, "Sessions"),
			    ]

		for aDir in theDirs:
			if os.path.exists(aDir):
				self.msg("\t%s already exists." % aDir)
			else:
				os.mkdir(aDir)
				self.msg("\t%s created." % aDir)

		# Copy the contents of the Cans directory from WebKit/Cans
		for name in glob.glob(os.path.join(self._webKitDir, "Cans", "*.py")):
			newname = os.path.join(self._workDir, "Cans", os.path.basename(name))
			shutil.copyfile(name, newname)

		self.msg("\n")



	def makeConfigFiles(self):
		"""
		Make all the default configuration files from templates located below stuffing in
		appropriate path names.
		"""
		self.msg("Creating default config files.")
		configInfo = [ ("AppServer", _AppServer_config),
			       ("Application", _Application_config),
			       ("CGIAdapter", _CGIAdapter_config),
			       ("FGCIAdapter", _FGCIAdapter_config),
			       ("ModPythonAdapter", _ModPythonAdapter_config),
			       ("OneShotAdapter", _OneShotAdapter_config),
			       ]

		for name, config in configInfo:
			name = os.path.join(self._workDir, "Configs", name+".config")
			open(name, "w").write(config % self._substVals)
			self.msg("\t%s created." % name)

		self.msg("\n")



	def makeLauncherScripts(self):
		"""
		Using templates loacted below, make scripts and/or batch files for
		launching the AppServer in various ways.  Also makes scripts suitable
		for use with the CGI adapters, etc.  In either case the Webware and
		the runtime directories are embedded in the scripts where needed.
		"""
		self.msg("Creating launcher scripts.")
		scripts = [ ("Launch.py", _Launch_py),
			    ("AppServer", _AppServer_sh),
			    ("AppServer.bat", _AppServer_bat),
			    ("HTTPServer", _HTTPServer_sh),
			    ("HTTPServer.bat", _HTTPServer_bat),
			    ]
		for name, template in scripts:
			name = os.path.join(self._workDir, name)
			open(name, "w").write(template % self._substVals)
			os.chmod(name, 0755)
			self.msg("\t%s created." % name)


		cgis = [ ("OneShot.cgi", "OneShotAdapter"),
			 ("WebKit.cgi",	 "CGIAdapter"),
			 ]
		for name, adapter in cgis:
			name = os.path.join(self._workDir, name)
			vals = self._substVals.copy()
			vals["ADAPTER"] = adapter
			open(name, "w").write(_X_cgi % vals)
			os.chmod(name, 0755)
			self.msg("\t%s created." % name)

		self.msg("\n")


	def copyOtherFiles(self):
		"""
		Make a copy of any other necessary files in the new work dir.
		"""
		for wildname in ["404Text.txt"]:  # relative to the webkit dir, can be wildcards
			for name in glob.glob(os.path.join(self._webKitDir, wildname)):
				newname = os.path.join(self._workDir, os.path.basename(name))
				shutil.copyfile(name, newname)


	def makeDefaultContext(self):
		"""
		Make a very simple context for the newbie user to play with.
		"""
		if self._sample is not None:
			self.msg("Creating default context.")
			name = os.path.join(self._workDir, self._sample)
			if not os.path.exists(name):
				os.mkdir(name)
			name2 = os.path.join(name, 'Main.py')
			open(name2, "w").write(_Main_py % self._substVals)

			name2 = os.path.join(name, '__init__.py')
			open(name2, "w").write(_init_py)



	def printCompleted(self):
		print """\n\n
Congratulations, you've just created a runtime working directory for
Webware.  To get started quickly you can run these commands:

	cd %(WORKDIR)s
	HTTPServer

and then point your browser to http://localhost:8086/.	The page you
see is generated from the code in the %(DEFAULT)s directory and is
there for you to play with and to build upon.

For a more robust solution, run the AppServer script and then copy
WebKit.cgi to your web server's cgi-bin directory, or anywhere else
that it will execute CGIs from.	 There are also several adapters in
the  Webware/WebKit directory that allow you to connect from the web
server to the WebKit AppServer without using CGI.

Have fun!
""" % self._substVals


	def msg(self, text):
		if self._verbose:
			print text



#----------------------------------------------------------------------
# TODO:	 These are currently just copies of the default WebKit Config
#	 files, adapted for substitution of directory names.  It would
#	 be very nice to generate them from this script as well, or
#	 perhaps the other way around, so there only needs to be one
#	 copy of the default config text...

_AppServer_config = """
{
	'PrintConfigAtStartUp': 1,
	'Verbose':		1,
	'Host':			'127.0.0.1',
	'Port':			8086,
	'PlugIns':		[],
	'PlugInDirs':		['%(WEBWARE)s'],
	'StartServerThreads':	10,
	'MaxServerThreads':	20,
	'MinServerThreads':	5,
	'CheckInterval':	100,
}
"""


_Application_config = """
{
	'AdminPassword':	'webware', # Change This!
	'PrintConfigAtStartUp': 1,
	'DirectoryFile':	['index', 'Main'],
	'ExtensionsToIgnore':	['.pyc', '.pyo', '.py~', '.psp~', '.html~','.bak'],
	'LogActivity':		0,
	'ActivityLogFilename':	'Logs/Activity.csv',
	'ActivityLogColumns':	['request.remoteAddress', 'request.method', 'request.uri', 'response.size', 'servlet.name', 'request.timeStamp', 'transaction.duration', 'transaction.errorOccurred'],
	'Contexts':		{'default':	  '%(DEFAULT)s',
				 'Admin':	  '%(WEBKIT)s/Admin',
				 'Examples':	  '%(WEBKIT)s/Examples',
				 'Docs':	  '%(WEBKIT)s/Docs',
				 'Testing':	  '%(WEBKIT)s/Testing',
				 %(DEFCTX)s
				},

	'SessionStore':		'Dynamic',  # can be File or Dynamic or Memory
	'SessionTimeout':	       60,  # minutes
	'MaxDynamicMemorySessions': 10000, # maximum sessions in memory
	'DynamicSessionTimeout':       15, # minutes, specifies when to move sessions from memory to disk
	'IgnoreInvalidSession':		0,

	'ExtraPathInfo'	      :		0, # set to 1 to allow extra path info to be attached to URLs


	'CacheServletClasses':		1, # set to 0 for debugging
	'CacheServletInstances':	1, # set to 0 for debugging

	# Error handling
	'ShowDebugInfoOnErrors':  1,
	'IncludeFancyTraceback':  0, # Requires cgitb.py module, downloadable from http://web.lfw.org/python/
	                             # If not using Python 2.1, also requires inspect.py and pydoc.py, also
	                             # available from the same site.
	'FancyTracebackContext': 5,
	'UserErrorMessage':	  'The site is having technical difficulties with this page. An error has been logged, and the problem will be fixed as soon as possible. Sorry!',
	'ErrorLogFilename':	  'Logs/Errors.csv',
	'SaveErrorMessages':	  1,
	'ErrorMessagesDir':	  'ErrorMsgs',
	'EmailErrors':		  0, # be sure to review the following settings when enabling error e-mails
	'ErrorEmailServer':	  'mail.-.com',
	'ErrorEmailHeaders':	  { 'From':	    '-@-.com',
				    'To':	    ['-@-.com'],
				    'Reply-to':	    '-@-.com',
				    'Content-type': 'text/html',
				    'Subject':	    'Error',
				  },
	'UnknownFileTypes': {
		'ReuseServlets': 1,

		# Technique choices:
		# serveContent, redirectSansAdapter
		'Technique': 'serveContent',

		# If serving content:
		'CacheContent': 1,  # set to 0 to reduce memory use
		'CheckDate':	1,
	},

	'IncludeTracebackInXMLRPCFault': 1,
}
"""


# The rest don't care about any pathnames, but are just here for completness

_CGIAdapter_config = """
{
		'NumRetries':		 20,
		'SecondsBetweenRetries': 3
}
"""


_FGCIAdapter_config = """
{
		'NumRetries':		 20,
		'SecondsBetweenRetries': 3
}
"""


_ModPythonAdapter_config = """
{
		'NumRetries':		 20,
		'SecondsBetweenRetries': 3
}
"""


_OneShotAdapter_config = """
{
	'ShowConsole':		 0,
	'ConsoleWidth':		 80,  # use 0 to turn off word wrap
	'ConsoleHangingIndent':	 4,
}
"""

#----------------------------------------------------------------------
# TODO:	 Just as above, the default copies of these files should be
#	 generated from here so there is only one copy.


_Launch_py = """\
#!/usr/bin/env python

import os, sys

def usage():
	print 'error: Launch.py (of WebKit)'
	print 'usage: Launch.py SERVER ARGS'
	sys.exit(1)

def main(args):
	if len(args) < 2:
		usage()
	server = args[1]
	if server[-3:]=='.py':
		server = server[:-3]
	sys.path.insert(0, '%(WEBWARE)s')
	import WebKit
	code = 'from WebKit.%%s import main' %% server
	exec code
	args = [''] + args[2:] + ['work=%(WORKDIR)s']
	main(args)

if __name__=='__main__':
	main(sys.argv)
"""


_AppServer_sh = """\
#!/bin/sh
/usr/bin/env python Launch.py AsyncThreadedAppServer $*
"""


_AppServer_bat = """\
python Launch.py ThreadedAppServer %%1 %%2 %%3 %%4 %%5
"""


_HTTPServer_sh = """\
#!/bin/sh
/usr/bin/env python Launch.py AsyncThreadedHTTPServer $*
"""


_HTTPServer_bat = """\
python Launch.py AsyncThreadedHTTPServer %%1 %%2 %%3 %%4 %%5
"""


# This can make both the OneShot.cgi and WebKit.cgi files
_X_cgi = """\
#!/usr/bin/env python

WebwareDir = '%(WEBWARE)s'
AppWorkDir = '%(WORKDIR)s'

try:
	import os, sys
	if WebwareDir:
		sys.path.insert(1, WebwareDir)
	else:
		WebwareDir = os.path.dirname(os.getcwd())
	webKitDir = os.path.join(WebwareDir, 'WebKit')
	if AppWorkDir is None:
		AppWorkDir = webKitDir
	import WebKit.%(ADAPTER)s
	WebKit.%(ADAPTER)s.main(AppWorkDir)
except:
	import string, sys, traceback
	from time import asctime, localtime, time

	sys.stderr.write('[%%s] [error] WebKit: Error in adapter\\n' %% asctime(localtime(time())))
	sys.stderr.write('Error while executing script\\n')
	traceback.print_exc(file=sys.stderr)

	output = apply(traceback.format_exception, sys.exc_info())
	output = string.join(output, '')
	output = string.replace(output, '&', '&amp;')
	output = string.replace(output, '<', '&lt;')
	output = string.replace(output, '>', '&gt;')
	output = string.replace(output, '\"', '&quot;')
	sys.stdout.write('''Content-type: text/html

<html><body>
<p>ERROR
<p><pre>%%s</pre>
</body></html>\\n''' %% output)
"""



#----------------------------------------------------------------------
# This is used to create a very simple sample context for the new
# work dir to give the newbie something easy to play with.

_init_py = """
def contextInitialize(appServer, path):
	# You could put initialization code here to be executed when
	# the context is loaded into WebKit.
	pass
"""

_Main_py = """
from WebKit.Page import Page

class Main(Page):

	def title(self):
		return 'My Sample Context'

	def writeBody(self):
		self.writeln('<h1>Welcome to Webware!</h1>')
		self.writeln('''
		This is a sample context generated for you and has purposly been kept very simple
		to give you something to play with to get yourself started.  The code that implements
		this page is located in <b>%%s</b>.
		''' %% self.request().serverSidePath())

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
			self.writeln('<li><a href="%%s/%%s/">%%s</a>' %% (adapterName, ctx, ctx))

		self.writeln('</ul>')

"""

#----------------------------------------------------------------------


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print __doc__
		sys.exit(1)

	# this assumes that this script is still located in Webware/bin
	p = os.path
	webWareDir = p.abspath(p.join(p.dirname(sys.argv[0]), ".."))

	mawd = MakeAppWorkDir(webWareDir, sys.argv[1])
	mawd.buildWorkDir()


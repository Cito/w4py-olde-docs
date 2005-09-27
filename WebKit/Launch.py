#!/usr/bin/env python

"""Launch.py

DESCRIPTION

Python launch script for the WebKit application server.

This launch script will run in its standard location in the Webware/WebKit
directory as well as in a WebKit work directory outside of the Webware tree.

USAGE

Launch.py [StartOptions] [AppServer [AppServerOptions]]

StartOptions:
  -d, --work-dir=...     Set the path to the app server working directory.
                         By default this is the directory containing Lauch.py.
  -w, --webware-dir=...  Set the path to the Webware root directory.
                         By default this is the parent directory.
  -l, --library=...      Other directories to be included in the search path.
                         You may specify this option multiple times.
  -p, --run-profile      Set this to get profiling going (see Profiler.py).
  -o, --log-file=...     Redirect standard output and error to this file.
  -i, --pid-file=...     Set the file path to hold the app server process id.
                         This option is fully supported under Unix only.
  -u, --user=...         The name or uid of the user to run the app server.
                         This option is supported under Unix only.
  -g, --group=...        The name or gid of the group to run the app server.
                         This option is supported under Unix only.

AppServer:
  The name of the application server module.
  By default, the ThreadedAppServer will be used.

AppServerOptions:
  Options that shall be passed to the application server.
  For instance, the ThreadedAppServer accepts: start, stop, daemon

Please note that the default values for the StartOptions and the AppServer
can be easily changed at the top of the Launch.py script.
"""

# FUTURE
# * This shares a lot of code with ThreadedAppServer.py and Launch.py.
#   Try to consolidate these things. The default settings below in the
#   global variables could go completely into AppServer.config.
# CREDITS
# * Contributed to Webware for Python by Chuck Esterbrook
# * Improved by Ian Bicking
# * Improved by Christoph Zwerschke


# You can change the following default values:

# The path to the app server working directory, if you do not
# want to use the directory containing this script:
workDir = None

# The path to the Webware root directory; by default this will
# be the parent directory of the directory containing this script:
webwareDir = None

# A list of additional directories (usually some libraries)
# that you want to include into the search path for modules:
libraryDirs = []

# To get profiling going, set runProfile = 1 (see also
# the description in the docstring of Profiler.py):
runProfile = 0

# The path to the log file, if you want to redirect the
# standard output and error to a log file:
logFile = None

# The pass to the pid file, if you want to check and terminate
# a running server by storing its server process id:
pidFile = None

# The name or uid of the server process user, if you want
# to run the server under a different user:
user = None

# The name or uid of the server process group, if you want
# to run the server under a different group:
group = None

# The default app server to be used:
appServer = 'ThreadedAppServer'


import os, sys

def usage():
	"""Print the docstring and exit with error."""
	sys.stdout.write(__doc__)
	sys.exit(2)

def launchWebKit(appServer=appServer, workDir=None, args=None):
	"""Import and launch the specified WebKit app server.

	appServer  -- the name of the WebKit app server module
	workDir -- the server-side work directory of the app server
	args -- other options that will be given to the app server

	"""
	# Set up the arguments for the app server:
	if args is None:
		args = []
	if workDir:
		args.append('workdir=' + workDir)
	# Allow for a .py on the server name:
	if appServer[-3:]=='.py':
		appServer = appServer[:-3]
	# Import the app server's main() function:
	try:
		appServerMain = __import__('WebKit.' + appServer, None, None, 'main').main
	except ImportError:
		print 'Error: Cannot import the app server module.'
		sys.exit(1)
	# Run the app server:
	appServerMain(args) # go!

def main(args=None):
	"""Evaluate the command line arguments and call launchWebKit."""
	global workDir, webwareDir, libraryDirs, runProfile, \
		logFile, pidFile, user, group, appServer
	if args is None:
		args = sys.argv[1:]
	# Get the name of the app server even if placed in front
	if args and not args[0].startswith('-'):
		appServer = args.pop(0)
	# Get all options:
	from getopt import getopt, GetoptError
	try:
		opts, args = getopt(args, 'd:w:l:po:i:u:g:', [
			'work-dir=', 'webware-dir=', 'library=', 'run-profile',
			'log-file=', 'pid-file=', 'user=', 'group='])
	except GetoptError, error:
		print str(error)
		usage()
	for opt, arg in opts:
		if opt in ('-d', '--work-dir'):
			workDir = arg
		elif opt in ('-w', '--webware-dir'):
			webwareDir = arg
		elif opt in ('-l', '--library'):
			libraryDirs.append(arg)
		elif opt in ('-p', '--run-profile'):
			runProfile = 1
		elif opt in ('-o', '--log-file'):
			logFile = arg
		elif opt in ('-i', '--pid-file'):
			pidFile = arg
		elif opt in ('-u', '--user'):
			user = arg
		elif opt in ('-g', '--group'):
			group = arg
	# Figure out the group id:
	gid = group
	if gid is not None:
		try:
			gid = int(gid)
		except ValueError:
			try:
				import grp
				entry = grp.getgrnam(gid)
			except KeyError:
				print 'Error: Group %r does not exist.' % gid
				sys.exit(2)
			except ImportError:
				print 'Error: Group names are not supported.'
				sys.exit(2)
			gid = entry[2]
	# Figure out the user id:
	uid = user
	if uid is not None:
		try:
			uid = int(uid)
		except ValueError:
			try:
				import pwd
				entry = pwd.getpwnam(uid)
			except KeyError:
				print 'Error: User %r does not exist.' % uid
				sys.exit(2)
			except ImportError:
				print 'Error: User names are not supported.'
				sys.exit(2)
			if not gid:
				gid = entry[3]
			uid = entry[2]
	# Figure out the work directory and make it the current directory:
	if workDir:
		workDir = os.path.expanduser(workDir)
	else:
		scriptName = sys.argv and sys.argv[0]
		if not scriptName or scriptName == '-c':
			scriptName = 'Launch.py'
		workDir = os.path.dirname(os.path.abspath(scriptName))
	try:
		os.chdir(workDir)
	except OSError, error:
		print 'Error: Could not set working directory.'
		print 'The path %r cannot be used.' % workDir
		print error.strerror
		print 'Check the --work-dir option.'
		sys.exit(1)
	workDir = os.path.curdir
	# Expand user components in directories:
	if webwareDir:
		webwareDir = os.path.expanduser(webwareDir)
	else:
		webwareDir = os.pardir
	if libraryDirs:
		libraryDirs = map(os.path.expanduser, libraryDirs)
	# Remove the package component in the name of this module,
	# because otherwise the package path would be used for imports, too:
	global __name__
	name = __name__.split('.')[-1]
	if name != __name__:
		sys.modules[name] = sys.modules[__name__]
		del sys.modules[__name__]
		__name__ = name
	# Check the validity of the Webware directory:
	sysPath = sys.path # memorize the standard Python search path
	sys.path = [webwareDir] # now include only the Webware directory
	try: # check whether Webware is really located here
		from Properties import name as webwareName
		from WebKit.Properties import name as webKitName
	except ImportError:
		webwareName = None
	if webwareName != 'Webware for Python' or webKitName != 'WebKit':
		print 'Error: Cannot find the Webware directory.'
		print 'The path %r seems to be wrong.' % webwareDir
		print 'Check the --webware-dir option.'
		sys.exit(1)
	if not os.path.exists(os.path.join(webwareDir, 'install.log')):
		print 'Error: Webware has not been installed.'
		print 'Please run install.py in the Webware directory:'
		print '> cd', os.path.abspath(webwareDir)
		print '> python install.py'
		sys.exit(1)
	# Now assemble a new clean Python search path:
	path = [] # the new search path will be collected here
	absPath = [] # the absolute pathes
	absWebKitDir = os.path.abspath(os.path.join(webwareDir, 'WebKit'))
	for p in ['', webwareDir] + libraryDirs + sysPath:
		ap = os.path.abspath(p)
		if ap == absWebKitDir: # do not include the WebKit directory
			continue
		if ap not in absPath: # include every path only once
			path.append(p)
			absPath.append(ap)
	sys.path = path # set the new search path
	# Get the name of the app server module:
	try:
		appServer = args.pop(0)
	except IndexError:
		pass # use the default value
	# Prepare the arguments for launchWebKit:
	args = (appServer, workDir, args)
	# Handle the pid file:
	if pidFile:
		pidFile = os.path.expanduser(pidFile)
		# Read the old pid file:
		try:
			pid = int(open(pidFile).read())
		except:
			pid = None
		if pid:
			print 'According to the pid file, the server is still running.'
			# Try to kill an already running server:
			killed = 0
			try:
				from signal import SIGTERM, SIGKILL
				print 'Trying to terminate the server with pid %d...' % pid
				os.kill(pid, SIGTERM)
			except OSError, error:
				from errno import ESRCH
				if error.errno == ESRCH: # no such process
					print 'The pid file was stale, continuing with startup...'
					killed = 1
				else:
					print 'Cannot terminate server with pid %d.' % pid
					print error.strerror
					sys.exit(1)
			except (ImportError, AttributeError):
				print 'Cannot check or terminate server with pid %d.' % pid
				sys.exit(1)
			if not killed:
				from time import sleep
				try:
					for i in range(100):
						sleep(0.1)
						os.kill(pid, SIGTERM)
				except OSError, error:
					from errno import ESRCH
					if error.errno == ESRCH:
						print 'Server with pid %d has been terminated.' % pid
						killed = 1
			if not killed:
				try:
					for i in range(100):
						sleep(0.1)
						os.kill(pid, SIGKILL)
				except OSError, error:
					from errno import ESRCH
					if error.errno == ESRCH:
						print 'Server with pid %d has been killed by force.' % pid
						killed = 1
			if not killed:
				print 'Server with pid %d cannot be terminated.' % pid
				sys.exit(1)
		# Write a new pid file:
		try:
			open(pidFile, 'w').write(str(os.getpid()))
		except:
			print 'The pid file %r could not be written.' % pidFile
			sys.exit(1)
	olduid = oldgid = stdout = stderr = log = None
	try:
		# Change server process group:
		if gid is not None:
			try:
				oldgid = os.getgid()
				if gid != oldgid:
					os.setgid(gid)
					if group:
						print 'Changed server process group to %r.' % group
				else:
					oldgid = None
			except:
				if group:
					print 'Could not set server process group to %r.' % group
					raise
					oldgid = None
					sys.exit(1)
		# Change server process user:
		if uid is not None:
			try:
				olduid = os.getuid()
				if uid != olduid:
					os.setuid(uid)
					print 'Changed server process user to %r.' % user
				else:
					olduid = None
			except:
				print 'Could not change server process user to %r.' % user
				olduid = None
				sys.exit(1)
		print 'Starting WebKit.%s...' % appServer
		# Handle the log file:
		if logFile:
			logFile = os.path.expanduser(logFile)
			try:
				log = open(logFile, 'a', 1) # append, line buffered mode
				print 'Output has been redirected to %r...' % logFile
				stdout, stderr = sys.stdout, sys.stderr
				sys.stdout = sys.stderr = log
			except IOError, error:
				print 'Cannot redirect output to %r.' % logFile
				print error.strerror
				log = None
				sys.exit(1)
		else:
			print
		# Set up a reference to our profiler so apps can import and use it:
		from WebKit import Profiler
		from time import time
		Profiler.startTime = time()
		# Now start the app server:
		if runProfile:
			print 'Profiling is on. See docstring in Profiler.py for more info.'
			print
			from profile import Profile
			profiler = Profile()
			Profiler.profiler = profiler
			Profiler.runCall(launchWebKit, *args)
			Profiler.dumpStats()
		else:
			launchWebKit(*args)
	finally:
		# Close the log file properly:
		if log:
			sys.stdout, sys.stderr = stdout, stderr
			log.close()
		# Restore server process group:
		if oldgid is not None:
			try:
				os.setgid(oldgid)
			except:
				pass
		# Restore server process user:
		if olduid is not None:
			try:
				os.setuid(olduid)
			except:
				pass
		# Remove the pid file again:
		if pidFile:
			try:
				os.remove(pidFile)
			except:
				print 'The pid file could not be removed.'

if __name__ == '__main__':
	main()

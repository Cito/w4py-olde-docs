#!/usr/bin/env python

"""checksrc.py


INTRODUCTION

This utility checks for violations of various source code conventions
in the hope of keeping the project clean and consistent.
Please see Webware/Documentation/StyleGuidelines.html for more information
including some guidelines not checked for by this utility.


COMMAND LINE

Running this program from the command line with -h will give you usage/help:
	> python checksrc.py -h

Examples:
	> python checksrc.py
	> python checksrc.py SomeDir
	> python checksrc.py -R SomeDir
	> python checksrc.py . results.text

And often you run it from the Webware directory like so:
	> cd Webware
	> python bin/checksrc.py


AS A MODULE AND CLASS

If you imported this as a module, you would use the CheckSrc class,
possibly like so:
	from CheckSrc import CheckSrc
	CheckSrc().check()

	# or:
	cs = CheckSrc()
	if cs.readArgs():
		cs.check()

	# or:
	cs = CheckSrc()
	cs.setOutput('results.text')
	cs.check()

And of course, you could subclass CheckSrc() to customize it,
which is why even command line utils get done with classes
(rather than collections of functions and nekkid code).

You can also setDirectory(), setOutput() setRecurse() and setVerbose()
the defaults of which are '.', sys.stdout, 1 and 0.


CAVEATS

Note that checksrc.py takes a line oriented approach. Since it does not
actually properly parse Python code, it can be fooled in some cases.
Therefore, it's possible to get false alarms. While we could implement
a full parser to close the gap, doing so would be labor intensive with
little pay off. So we live with a few false alarms.


CONFIG FILES

You can modify the behavior of checksrc.py for a particular directory
by creating a .checksrc.config file like so:

{
	'SkipDirs': ['Cache'],
	'SkipFiles': ['fcgi.py', 'zCookieEngine.py'],
	'DisableErrors': {
		'UncapFN': '*',
		'ExtraUnder': ['MiddleObject'],
	}
}

Some notes:
	* You can specify some or all of the options.
	* SkipDirs and SkipFiles both require lists of filenames.
	* DisableError keys are error codes defined by checksrc.py.
	  You can find these out by running checksrc with the
	  -h command line option or checking the source below.
	* The value for disabling an error:
		* Can be an individual filename or a list of filenames.
		* Can be '*' for "all files".


RULES

	X File names start with capital letter.
	X (On POSIX) Files don't contain \r.
	X Spaces are not used for indentation.
	X Tabs are used only for initial indentation.
	X Class names start with a capital letter.
	X Method names start with a lower case letter.
	X Methods do not start with "get".
	X Data attributes start with an underscore _.
	X Method and attribute names have no underscores after the first character.
	X Expressions following if, while and return
	  are not enclosed in parenthesees, ().
	- Data attributes not only start with an underscore _,
	  but are followed by a lower case letter.
	- Class defs and category comments, ## Like this ##
	  are preceded by 2 blank lines and are followed by one blank line
	  (unless the class implementation is pass).


FUTURE

Implement the spacing checks for class defs and category comments.

Consider setting _charNum for the current location.

Consider (optionally) displaying the source line.

Maybe: Experiment with including the name of the last seen method/function
with the error messages to help guide the user to where the error occurred.

"""


import re, sys, os
from types import StringType


class NoDefault:
	pass


class CheckSrc:

	errors = {
		'UncapFN': 'Uncapitalized filename.',
		'CarRet': 'Carriage return \\r found.',
		'StrayTab': 'Stray tab after other characters.'
			' No tabs allowed other than initial indentation.',
		'SpaceIndent': 'Found space as part of indentation. Use only tabs.',
		'ClassNotCap': 'Class names should start with capital letters.',
		'MethCap': 'Method name "%(name)s" should start with lower case letter.',
		'GetMeth': 'Method name "%(name)s" should not start with "get".',
		'NoUnderAttr': 'Data attributes should start with underscores: %(attribute)s.',
		'ExtraUnder': 'Attributes and methods should not have underscores'
			' past the first character: %(attribute)s.',
		'ExtraParens': 'No outer parenthesees should be used for %(keyword)s.',
	}


	## Init ##

	def __init__(self):
		# See checkAttrNames() for the use of the following REs

		# This RE matches access of self that does not start with an
		# underscore and does not end in (, indicating a method. For
		# example, self.foo. This violates one the rules: data
		# attributes should start with an underscore.
		self._badAccessRE = re.compile(r'self\.[A-Za-z0-9][\w]*[^(]')

		# This RE matches any kind of access of self
		self._accessRE = re.compile(r'self\.[\w]+')

		# Grab our own copy of errors with lower case keys
		self._errors = {}
		self._errorCodes = []
		for (key, value) in self.__class__.errors.items():
			self._errorCodes.append(key)
			self._errors[key.lower()] = value

		# Misc init
		self._config = {}

		# Set default options
		self.setDirectory('.')
		self.setOutput(sys.stdout)
		self.setRecurse(1)
		self.setVerbose(0)


	## Options ##

	def directory(self):
		return self._directory

	def setDirectory(self, dir):
		"""Sets the directory that checking starts in."""
		self._directory = dir

	def output(self):
		return self._out

	def setOutput(self, output):
		"""Set the destination output.

		It can either be an object which must respond to write() or
		a string which is a filename used for one invocation of check().

		"""
		if type(output) is StringType:
			self._out = open(output, 'w')
			self._shouldClose = 1
		else:
			self._out = output
			self._shouldClose = 0

	def recurse(self):
		return self._recurse

	def setRecurse(self, flag):
		"""Set whether or not to recurse into subdirectories."""
		self._recurse = flag

	def verbose(self):
		return self._verbose

	def setVerbose(self, flag):
		"""Set whether or not to print extra information during check.

		For instance, print every directory and file name scanned.
		"""
		self._verbose = flag


	## Command line use ##

	def readArgs(self, args=sys.argv):
		"""Read a list of arguments in command line style (e.g., sys.argv).

		You can pass your own args if you like, otherwise sys.argv is used.
		Returns 1 on success; 0 otherwise.

		"""
		setDir = setOut = 0
		for arg in args[1:]:
			if arg == '-h' or arg == '--help':
				self.usage()
				return 0
			elif arg == '-r':
				self.setRecurse(1)
			elif arg == '-R':
				self.setRecurse(0)
			elif arg == '-v':
				self.setVerbose(1)
			elif arg == '-V':
				self.setVerbose(0)
			elif arg[0] == '-':
				self.usage()
				return 0
			else:
				if not setDir:
					self.setDirectory(arg)
					setDir = 1
				elif not setOut:
					self.setOutput(arg)
					setOut = 1
				else:
					self.write('Error: %s\n' % repr(arg))
					self.usage()
					return 0
		return 1

	def usage(self):
		progName = sys.argv[0]
		wr = self.write
		wr('Usage: %s [options] [startingDir [outputFilename]]\n' % progName)
		wr('''       -h --help = help
       -r -R = recurse, do not recurse. default -r
       -v -V = verbose, not verbose. default -V

Examples:
    > python checksrc.py
    > python checksrc.py SomeDir
    > python checksrc.py -R SomeDir
    > python checksrc.py . results.text

Error codes and their messages:
''')

		# Print a list of error codes and their messages
		keys = self._errorCodes[:]
		keys.sort()
		maxLen = 0
		for key in keys:
			if len(key) > maxLen:
				maxLen = len(key)
		for key in keys:
			paddedKey = key.ljust(maxLen)
			wr('  %s = %s\n' % (paddedKey, self._errors[key.lower()]))
		wr('\n')

		wr('.checksrc.config options include SkipDirs, SkipFiles and DisableErrors.\nSee the checksrc.py doc string for more info.\n')


	## Printing, errors, etc. ##

	def write(self, *args):
		"""Invoked by self for all printing.

		This allows output to be easily redirected.

		"""
		write = self._out.write
		for arg in args:
			write(str(arg))

	def error(self, msgCode, args):
		"""Invoked by self when a source code error is detected.

		Prints the error message and it's location.
		Does not raise exceptions or halt the program.

		"""
		# Implement the DisableErrors option
		disableNames = self.setting('DisableErrors', {}).get(msgCode, [])
		if '*' in disableNames or self._fileName in disableNames:
			return

		if not self._printedDir:
			self.printDir()
		msg = self._errors[msgCode.lower()] % args
		self.write(self.location(), msg, '\n')

	def fatalError(self, msg):
		"""Report a fatal error and raise CheckSrcError.

		For instance, handle an invalid configuration file.

		"""
		self.write('FATAL ERROR: %s\n' % msg)
		raise CheckSrcError

	def location(self):
		"""Return a string indicating the current location.

		The string format is "fileName:lineNum:charNum:".
		The string may be shorter if the latter components are undefined.

		"""
		s = ''
		if self._fileName is not None:
			s += self._fileName
			if self._lineNum is not None:
				s += ':' + str(self._lineNum)
				if self._charNum is not None:
					s += ':' + str(self._charNum)
		if s:
			s += ':'
		return s

	def printDir(self):
		"""Self utility method to print the directory being processed."""
		self.write('\n', self._dirName, '\n')
		self._printedDir = 1


	## Configuration ##

	def readConfig(self, dirName):
		filename = os.path.join(dirName, '.checksrc.config')
		try:
			contents = open(filename).read()
		except IOError:
			return
		try:
			dict = eval(contents)
		except:
			self.fatalError('Invalid config file at %s.' % filename)
		# For DisableErrors, we expect a dictionary keyed by error codes.
		# For each code, we allow a value that is either a string or a list.
		# But for ease-of-use purposes, we now convert single strings to
		# lists containing the string.
		de = dict.get('DisableErrors', None)
		if de:
			for key, value in de.items():
				if type(value) is StringType:
					de[key] = [value]

		self._config = dict

	def setting(self, name, default=NoDefault):
		if default == NoDefault:
			return self._config[name]
		else:
			return self._config.get(name, default)


	## Checking ##

	def check(self):
		if self._recurse:
			os.path.walk(self._directory, self.checkDir, None)
		else:
			self.checkDir(None, self._directory, os.listdir(self._directory))
		if self._shouldClose:
			self._out.close()

	def checkDir(self, arg, dirName, names):
		"""Invoked by os.path.walk() which is kicked off by check().

		Recursively checks the given directory and all it's subdirectories.

		"""
		# Initialize location attributes.
		# These are updated while processing and
		# used when reporting errors.
		self._dirName = dirName
		self._fileName = None
		self._lineNum = None
		self._charNum = None
		self._printedDir = 0

		if self._verbose:
			self.printDir()

		self.readConfig(dirName)

		# Prune directories based on configuration
		skipDirs = self.setting('SkipDirs', [])
		for dir in skipDirs:
			try:
				index = names.index(dir)
			except ValueError:
				continue
			print '>> skipping', dir
			del names[index]

		skipFiles = self.setting('SkipFiles', [])
		for name in names:
			if len(name) > 2 and name[-3:] == '.py' and name not in skipFiles:
				try:
					self.checkFile(dirName, name)
				except CheckSrcError:
					pass

	def checkFile(self, dirName, name):
		self._fileName = name
		if self._verbose:
			self.write('  %s\n' % self._fileName)

		self.checkFilename(name)

		filename = os.path.join(dirName, name)
		contents = open(filename, 'rb').read()
		self.checkFileContents(contents)

		lines = open(filename).readlines()
		self.checkFileLines(lines)

	def checkFilename(self, filename):
		if filename[0] != filename[0].upper():
			self.error('UncapFN', locals())

	def checkFileContents(self, contents):
		if os.name == 'posix':
			if '\r' in contents:
				self.error('CarRet', locals())

	def checkFileLines(self, lines):
		self._lineNum = 1
		inMLS = None # MLS = multi-line string
		for line in lines:
			lineleft = line.lstrip()
			if lineleft and not lineleft[0] == '#':
				index = 0
				wholeLineInMLS = inMLS
				while index != -1:
					if inMLS:
						index = lineleft.find(inMLS, index)
						if index != -1:
							wholeLineInMLS = inMLS = None
							index += 3
					else:
						index2 = lineleft.find('"""', index)
						if index2 != -1:
							index = lineleft.find("'''", index)
							if index != -1 and index < index2:
								inMLS= "'''"
							else:
								index = index2
								inMLS = '"""'
							index += 3
						else:
							index = lineleft.find("'''", index)
							if index != -1:
								inMLS = "'''"
								index += 3
				if not wholeLineInMLS:
					self.checkFileLine(line)
			self._lineNum += 1

	def checkFileLine(self, line):
		self.checkTabsAndSpaces(line)
		self.checkClassName(line)
		self.checkMethodName(line)
		self.checkExtraParens(line)

	def checkTabsAndSpaces(self, line):
		foundTab = foundSpace = foundOther = 0
		for c in line:
			if c == '\t':
				foundTab = 1
				if foundSpace or foundOther:
					self.error('StrayTab', locals())
					break
			elif c == ' ':
				foundSpace = 1
				if not foundOther:
					self.error('SpaceIndent', locals())
					break
			else:
				foundOther = 1

	def checkClassName(self, line):
		if line.find('class') != -1:
			parts = line.split()
			if 'class' in parts: # e.g. if 'class' is a standalone word
				index = parts.index('class')
				if index == 0: # e.g. if start of the line
					name = parts[1]
					if name and name[0] != name[0].upper():
						self.error('ClassNotCap', locals())

	def checkMethodName(self, line):
		if line.find('def') != -1:
			parts = line.split()
			if 'def' in parts: # e.g. if 'def' is a standalone word
				index = parts.index('def')
				if index == 0 and line[0] == '\t':
					# e.g. if start of the line, and indented (indicating method and not function)
					name = parts[1]
					name = name[:name.find('(')]
					if name and name[0] != name[0].lower():
						self.error('MethCap', locals())
					if len(name) > 3 and name[:3].lower() == 'get':
						self.error('GetMeth', locals())

	def checkAttrNames(self, line):
		# Attribute names that are data (and not methods) should start with an underscore.
		text = line
		while text:
			match = self._badAccessRE.search(text)
			if match:
				try:
					nextChar = text[match.end()]
				except IndexError:
					nextChar = ''
				attribute = match.group()
				if nextChar != '(':
					self.error('NoUnderAttr', locals())

			# Next
			text = text[match.end():]

		# No attribute name should have an underscore after the first character
		while text:
			# Try to find a self.access
			match = self._accessRE.search(text)
			if not match:
				break

			# Check it for violations
			group = match.group()
			if '_' in group[6:]:
				bad = 1
				# Make sure it's not one of those __foo__ identifiers.
				group = group[5:] # shave off "self."
				if len(group) > 4 and group[:2] == '__' and group[-2:] == '__':
					if not '_' in group[2:-2]:
						bad = 0
				if bad:
					self.error('ExtraUnder', locals())

			# Next
			text = text[match.end():]

	def checkExtraParens(self, line):
		keywords = ['if', 'while', 'return']
		msg = ', '.join(keywords[:-1]) + ' and ' + keywords[-1]
		parts = line.split()
		if (len(parts) > 1 and parts[0] in keywords
				and parts[1][0] == '('
				and not line.count(')') < line.count('(')):
			keyword = parts[0]
			self.error('ExtraParens', locals())


class CheckSrcError(Exception):
	pass


class _DummyWriter:

	def write(self, msg):
		pass


if __name__ == '__main__':
	cs = CheckSrc()
	if cs.readArgs():
		cs.check()

#!/usr/bin/env python
'''
Generate.py

> python Generate.py -h
'''


import os, string, sys
from string import split, upper
from getopt import getopt


def FixPathForMiddleKit():
	import os, sys
	if globals().has_key('__file__'):
		# We were imported as a module
		location = __file__
	else:
		# We were executed directly
		location = sys.argv[0]

	# location will basically be:
	# .../MiddleKit/Design/Generate.py
	v = 0  # verbose
	if v: print 'location =', location
	if location.find('MiddleKit')!=-1:
		if v: print '>> MiddleKit in location'
		index = location.index('MiddleKit')
		location = location[:index]
		if v: print 'new location =', location
	location = os.path.abspath(os.path.normpath(location))
	if v: print 'final location =', location
	sys.path.insert(1, location)
	sys.path.insert(1, 'D:/cvs/Projects/Dev/')
	if v: print 'path =', sys.path
	if v: print
	if v: print 'importing MiddleKit...'
	import MiddleKit
	if v: print 'done.'

try:
	import MiddleKit
except:
	FixPathForMiddleKit()

# 2000-10-14 ce: DUPLICATED IN MiddleKit/Tests/Test.py
def FixPathForConfigurable():
	import os, sys
	home = os.environ['HOME']
	pjoin = os.path.join
	norm = os.path.normpath
	if len(sys.path) and sys.path[0]=='':
		index = 1
	else:
		index = 0
	sys.path.insert(index, norm(pjoin(home, 'Projects/Webware')))
	sys.path.insert(index, norm(pjoin(home, 'Projects/Webware/WebKit')))

try:
	import Configurable
except:
	FixPathForConfigurable()


class Generate:

	def databases(self):
		return ['MySQL']  # @@ 2000-10-19 ce: should build this dynamically

	def main(self, args=sys.argv):
		opt = self.options(args)

		# Make or check the output directory
		outdir = opt['outdir']
		if not os.path.exists(outdir):
			os.mkdir(outdir)
		elif not os.path.isdir(outdir):
			print 'Error: Output target, %s, is not a directory.' % outdir

		# Generate
		self.generate('SQL', opt, 'sql', 'SQLGenerator', os.path.join(outdir, 'GeneratedSQL'))
		self.generate('Python', opt, 'py', 'PythonGenerator', outdir)

	def usage(self, errorMsg=None):
		progName = os.path.basename(sys.argv[0])
		if errorMsg:
			print '%s: error: %s' % (progName, errorMsg)
		print 'Usage: %s --db DBNAME --model FILENAME [--sql] [--py] [--outdir DIRNAME]' % progName
		print '       %s -h | --help' % progName
		print
		print '       * Known databases include: %s.' % ','.join(self.databases())
		print '       * If neither --sql nor --py are specified, both are generated.'
		print '       * If --outdir is not specified, then the base filename (sans extension) is used.'
		print
		sys.exit(1)

	def options(self, args):
		# Command line dissection
		if type(args)==type(''):
			args = args.split()
		optPairs, files = getopt(args[1:], 'h', ['help', 'db=', 'model=', 'sql', 'py', 'outdir='])
		if len(optPairs)<1:
			self.usage('Missing options.')
		if len(files)>0:
			self.usage('Extra files or options passed.')

		# Turn the cmd line optPairs into a dictionary
		opt = {}
		for key, value in optPairs:
			if len(key)>=2 and key[:2]=='--':
				key = key[2:]
			elif key[0]=='-':
				key = key[1:]
			opt[key] = value

		# Check for required opt, set defaults, etc.
		if opt.has_key('h') or opt.has_key('help'):
			self.usage()
		if not opt.has_key('db'):
			self.usage('No database specified.')
		if not opt.has_key('model'):
			self.usage('No model specified.')
		if not opt.has_key('sql') and not opt.has_key('py'):
			opt['sql'] = ''
			opt['py'] = ''
		if not opt.has_key('outdir'):
			opt['outdir'] = os.curdir

		return opt

	def generate(self, name, opt, cmdLineOption, className, outdir):
		if opt.has_key(cmdLineOption):
			print 'Generating %s...' % name
			name = opt['db'] + className
			module = __import__(name, globals())
			klass = getattr(module, name)
			generator = klass()
			generator.readModelFileNamed(opt['model'])
			generator.generate(outdir)


if __name__=='__main__':
	Generate().main(sys.argv)

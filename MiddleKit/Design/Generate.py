#!/usr/bin/env python
'''
Generate.py

> python Generate.py -h
'''


import os, string, sys
from string import split, upper
from getopt import getopt


def FixPathForMiddleKit(verbose=0):
	'''
	Enhances sys.path so that Generate.py can import MiddleKit.whatever.
	We *always* enhance the sys.path so that Generate.py is using the MiddleKit that contains him, as opposed to whatever happens to be found first in the Python path. That's an subtle but important feature for those of us who sometimes have more than one MiddleKit on our systems.
	'''
	v = verbose
	import os, sys
	if globals().has_key('__file__'):
		# We were imported as a module
		location = __file__
		if v: print 'took location from __file__'
	else:
		# We were executed directly
		location = sys.argv[0]
		if v: print 'took location from sys.argv[0]'

	if v: print 'location =', location
	if location.lower()=='generate.py':
		# The simple case. We're at MiddleKit/Design/Generate.py
		location = os.path.abspath('../../')
	else:
		# location will basically be:
		# .../MiddleKit/Design/Generate.py
		if os.name=='nt':
			# Case insenstive file systems:
			location = location.lower()
			what = 'middlekit'
		else:
			what = 'MiddleKit'
		if location.find(what)!=-1:
			if v: print 'MiddleKit in location'
			index = location.index(what)
			location = location[:index]
			if v: print 'new location =', location
		location = os.path.abspath(location)
		if v: print 'final location =', location
	sys.path.insert(1, location)
	if v: print 'path =', sys.path
	if v: print
	if v: print 'importing MiddleKit...'
	import MiddleKit
	if v: print 'done.'

FixPathForMiddleKit()
import MiddleKit


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

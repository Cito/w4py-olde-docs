#!/usr/bin/env python

import os, sys

def usage():
#	sys.stdout = sys.stderr
	print 'error: Launch.py (of WebKit)'
	print 'usage: Launch.py SERVER ARGS'
	sys.exit(1)

def main(args):
	if len(args)<2:
		usage()
	server = args[1]
	os.chdir(os.pardir)
	if '' not in sys.path:
		sys.path = [''] + sys.path
	import WebKit
	code = 'from WebKit.%s import main' % server
	exec code
	args = args[2:]
	main(args)

if __name__=='__main__':
	main(sys.argv)

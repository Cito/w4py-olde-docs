#!/usr/bin/env python

import os, sys

def usage():
	print 'error: Launch.py (of WebKit)'
	print 'usage: Launch.py SERVER ARGS'
	sys.exit(1)

def main(args):
	if len(args)<2:
		usage()

	server = args[1] # the server

	# allow for a .py on the server name
	if server[-3:]=='.py':
		server = server[:-3]

	# figure out directory locations
	webKitDir = os.path.dirname(os.path.join(os.getcwd(), sys.argv[0]))
	webwareDir = os.path.dirname(webKitDir)

	# clean up sys.path
	def ok(directory):
		return directory not in ['', '.'] and directory[-6:].lower()!='webkit'
	sys.path = filter(ok, sys.path)
	#if not webwareDir in sys.path:
	#	sys.path.insert(0, webwareDir)
	sys.path.insert(0, '')

	# go to Webware dir so that:
	#   - importing packages like 'WebUtils' hits this Webware
	#   - we cannot import WebKit modules without qualifying them
	os.chdir(webwareDir)

	# Import the server's main()
	import WebKit
	code = 'from WebKit.%s import main' % server
	exec code
	args = args[2:]

	# Run!
	main(args)


if __name__=='__main__':
	main(sys.argv)

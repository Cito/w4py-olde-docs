#!/usr/bin/env python

import os, sys


def usage():
	print 'error: Launch.py (of WebKit)'
	print 'usage: Launch.py SERVER ARGS'
	sys.exit(1)


def launchWebKit(server, appWorkPath, args):
	"""
	Import and launch the specified WebKit server.
	"""
	# allow for a .py on the server name
	if server[-3:]=='.py':
		server = server[:-3]

	# clean up sys.path
	def ok(directory):
		return directory not in ['', '.'] and directory[-6:].lower()!='webkit'
	sys.path = filter(ok, sys.path)
	sys.path.insert(0, '')

	# Import the server's main()
	import WebKit
	code = 'from WebKit.%s import main' % server
	exec code

	# Run!
	args = args + ['workdir=' + appWorkPath]
	main(args)



def main(args):
	if len(args)<2:
		usage()

	server = args[1] # the server

	# figure out directory locations
	webKitPath = os.path.dirname(os.path.join(os.getcwd(), sys.argv[0]))
	webwarePath = os.path.dirname(webKitPath)

	# go to Webware dir so that:
	#   - importing packages like 'WebUtils' hits this Webware
	#   - we cannot import WebKit modules without qualifying them
	os.chdir(webwarePath)

	# Go!
	launchWebKit(server, webKitPath, args[2:])


if __name__=='__main__':
	main(sys.argv)

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
	if server[-3:]=='.py':
		server = server[:-3]
		
	if '' not in sys.path:
		sys.path = [''] + sys.path
	try:
		import WebwarePathLocation
		wwdir = os.path.abspath(os.path.join(os.path.dirname(WebwarePathLocation.__file__),".."))
	except Exception, e:
		print e
		usage()

	if not wwdir in sys.path:
		sys.path.insert(0,wwdir)
	import WebKit
	code = 'from WebKit.%s import main' % server
	exec code
	args = args[2:]
	main(args)

if __name__=='__main__':
	main(sys.argv)

#!/usr/bin/env python
'''
Used to generate the config sections for WebKit.html.
'''

import re, string, sys


def toc(filename):
	f = open(filename)
	contents = f.read()
	f.close()
	list = eval(contents)
	for item in list:
		name, default, descr = item
		print '<p><dl>'
		if len(default)<20:
			print '<dt><font face="Arial, Helvetica"><b>%s</b></font>' % name
			print '&nbsp; <code> = %s</code></dt>' % default
			print '<dd>'
			print '%s' % descr
			print '</dd>'
		else:
			print '<dt><font face="Arial, Helvetica"><b>%s</b></font></dt>' % name
			print '<dd>'
			print '<code>= %s</code>' % default
			print '<br> <hr> %s' % descr
			print '</dd>'		
		print '</dl></p>'
		print

def main(filename):
	# header
	print '<html> <head><title>Config</title></head> <body>'
	print '<p>'
	toc(filename)
	print '</body></html>'
	

if __name__=='__main__':
	for filename in sys.argv[1:]:
		main(filename)

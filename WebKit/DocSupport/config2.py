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
	print '<table border=2 align=center width=80% cellpadding=2 cellspacing=2>'
	for item in list:
		name, default, descr = item
		print '<tr valign=top>'
		if len(default)<20:
#			print '<td> %s </td> <td> <code>%s</code> </td> <td> %s </td>' % (name, default, descr)
			print '<td> <b>%s</b><br> &nbsp; &nbsp; <font size=-1>= %s</font> </td> <td> %s </td>' % (name, default, descr)
		else:
#			print '<td> %s </td> <td> --> </td> <td> <code>%s</code><br><hr>%s </td>' % (name, default, descr)
			print '<td> <b>%s</b><br> &nbsp; &nbsp; <font size=-1>--></font> </td> <td> <center><code>%s</code></center><hr>%s </td>' % (name, default, descr)
		print '</tr>'
	print '</table>'

def main(filename):
	# header
	print '<html> <head><title>Config</title></head> <body bgcolor=#EEEEEE>'
	print '<p>'
	toc(filename)
	print '</body></html>'
	

if __name__=='__main__':
	for filename in sys.argv[1:]:
		main(filename)

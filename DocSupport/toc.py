#!/usr/bin/env python
'''
Used to generate the table of contents for CGIWrapper.html.
'''


import re, string, sys


def usage():
	print 'usage: %s <input filename>' % sys.argv[0]
	sys.exit(1)

def toc(filename, indentFactor=3, fontSize=[None, None, '+1', '']):
	f = open(filename)
	expr = re.compile("(<a name=(.*)>)?<[hH]([1-9])>(.*)</[hH][1-9]>")
	while 1:
		line = f.readline()
		if not line:
			break
		match = expr.search(line)
		if match:
			#print 'match for:', string.strip(line)
			groups = match.groups()
			#print 'groups:', match.groups()
			identifier, level, name = groups[1:4]
			level = int(level)
			if level>1:
				indenter = '&nbsp; '*indentFactor*(level-2)
				print '<br> %s <a href="#%s"><font size=%s>%s</font></a>' % (indenter, identifier, fontSize[level], name)
			#print
	f.close()

def main(args):
	if len(args)<2:
		usage()
	# header
	print '<html> <head><title>TOC</title></head> <body>'
	print '<p><font face="Helvetica">'
	toc(args[1])
	print '</font></p>'
	print '</body></html>'
	

if __name__=='__main__':
	main(sys.argv)

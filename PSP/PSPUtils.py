
"""
A bunch of utility functions for the PSP generator.

--------------------------------------------------------------------------
   (c) Copyright by Jay Love, 2000 (mailto:jsliv@jslove.net)

	Permission to use, copy, modify, and distribute this software and its
	documentation for any purpose and without fee or royalty is hereby granted,
	provided that the above copyright notice appear in all copies and that
	both that copyright notice and this permission notice appear in
	supporting documentation or portions thereof, including modifications,
	that you make.

	THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD TO
	THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
	FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
	INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
	FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
	NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
	WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

		This software is based in part on work done by the Jakarta group.

"""

import string
import copy
import re

"""various utility functions"""



def removeQuotes(st):
	return string.replace(st,"%\\\\>","%>")

def isExpression(st):
	OPEN_EXPR = '<%='
	CLOSE_EXPR = '%>'
	
	if ((st[:len(OPEN_EXPR)] == OPEN_EXPR) and (st[-len(CLOSE_EXPR):] == CLOSE_EXPR)):
		return 1
	return 1

def getExpr(st):
	OPEN_EXPR = '<%='
	CLOSE_EXPR = '%>'
	length = len(st)
	if ((st[:len(OPEN_EXPR)] == OPEN_EXPR) and (st[-len(CLOSE_EXPR):] == CLOSE_EXPR)):
		retst = st[len(OPEN_EXPR):-(len(CLOSE_EXPR))]
	else:
		retst=''
	return retst


def checkAttributes(tagtype, attrs, validAttrs):

	#missing check for mandatory atributes
	#see line 186 in JSPUtils.java

	pass
	
	

RE_LINES = re.compile("[\n\r]*")
def splitLines( text ):
	'''
	Split text into lines, but works for Unix, or Windows format, 
	i.e. with \n or \r for line endings.
	'''
	return RE_LINES.split( text )



def normalizeIndentation( pySource ):
	'''
	Takes a block of code that may be too indented, and moved it all the the left.
	
	See PSPUtilsTest for examples.
	
	- Winston Wolff
	'''
	
	# split into lines, but keep \n and \r chars.
	lines = re.findall( "[^\n\r]*[\n\r]*", pySource)
	
	# find the line with the least indentation
	indent = 999	# This should be big enough
	for line in lines:

		lstripped = line.lstrip()
		
		# if line is empty or comment, don't measure the indentation
		if len(lstripped) == 0 or lstripped[0] == '#':
			continue
		indent = min( indent, len(line) - len(lstripped) )
		
	# Strip off the first 'indent' characters from each line
	strippedLines = []
	for line in lines:
	
		# Remove the first 'indent' whitespace chars, but not \n or \r
		charsToStrip = 0
		for i in range(0,min( indent, len(line)) ):
			if line[i] in ' \t':
				charsToStrip = charsToStrip+1
			else:
				break # don't check any more characters
			
		strippedLines.append( line[charsToStrip:] )
		
	# write lines back out
	result = ''.join(strippedLines)
	
	return result

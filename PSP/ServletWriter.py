"""
This module holds the actual file writer class.

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

from Context import *

import string, os, sys
from PSPReader import *

if sys.hexversion > 0x10502f0: py2=1
else:
	py2=0
	import tempfile

def maketempfilename(dir,ext):
	""" Trying to keep Py1.5 compatibility"""
	if py2:
		return os.tempnam(dir,ext)
	else:
		return tempfile.mktemp(ext)

class ServletWriter:
    
	''' This file creates the servlet source code. Well, it writes it out to a file at least.'''

	TAB = '\t'
	SPACES = '    ' # 4 spaces
	EMPTY_STRING=''
    
	def __init__(self,ctxt):
	
		self._pyfilename = ctxt.getPythonFileName()
		self._temp = maketempfilename(os.path.dirname(self._pyfilename), 'tmp.')
		self._filehandle = open(self._temp,'w+')
		self._tabcnt = 0
		self._blockcount = 0 # a hack to handle nested blocks of python code
		self._indentSpaces = self.SPACES
		self._useTabs=1
		self._useBraces=0
		self._indent='\t'
		self._userIndent = self.EMPTY_STRING

	def setIndentSpaces(self,amt):
		self._indentSpaces=' '*amt
		self.setIndention()

	def setIndention(self):
		if self._useTabs:
			self._indent='\t'
		else:
			self._indent=self._indentSpaces#' '*self._indentSpaces

	def setIndentType(self, type):
		if type=="tabs":
			self._useTabs=1
			self.setIndention()
		elif type=="spaces":
			self._useTabs=0
			self.setIndention()
		elif type=="braces":
			self._useTabs=0
			self._useBraces=1
			self.setIndention()
	
	def close(self):
		self._filehandle.close()
		os.rename(self._temp, self._pyfilename)

	def pushIndent(self):
		'''this is very key, have to think more about it'''
		self._tabcnt = self._tabcnt + 1

	def popIndent(self):
		if self._tabcnt > 0:
			self._tabcnt = self._tabcnt - 1
	    
	
	def printComment(self, start, stop, chars):

		if start and stop:
			self.println('## from ' + str(start))
			self.println('## from ' + str(stop))

		if chars:
			sp = string.split(chars,'\n')
			for i in sp:
				self._filehandle.write(self.indent(''))
				self._filehandle.write('##')
				self._filehandle.write(i)

	def quoteString(self, s):
		'''escape the string'''
		#None
		if s == None:
			return 'None'
			#this probably wont work, Ill be back for this
		return 'r'+s

	def indent(self,st):
		"""Added userIndent 6/18/00"""
		if self._tabcnt>0:
			return self._userIndent + self._indent*self._tabcnt +st
		return st
	
	def println(self, line=None):
		'''Prints with Indentation and a newline if none supplied'''
		if line:
			self._filehandle.write(self.indent(line))
		else:
			self._filehandle.write(self.indent('\n'))
	    
	
		if line and line[:-1] != '\n':
			self._filehandle.write('\n')

	def printChars(self, st):
		'''just prints what its given'''
		self._filehandle.write(st)

	def printMultiLn(self, st):
		raise 'NotImplemented Error'


	def printList(self, strlist):
		'''prints a list of strings with indentation and a newline'''
		for i in strlist:
			self.printChars(self.indent(i))
			self.printChars('\n')

	def printIndent(self):
		'''just prints tabs'''
		self.printChars(self.indent(''))
	

    
	

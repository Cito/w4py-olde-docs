"""
This module co-ordinates the reading of the source file.
It maintains the current position of the parser in the source file.

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

import types
import copy
import string
import os



class Mark:
	"""The Mark class marks a point in an input stream.
	DOES THIS NEED TO BE LINE BASED? Why is JSP doing this?"""

	def __init__(self, reader, linearray=None, fileid=None, stream=None, inBaseDir=None, encoding=None):
		
		if isinstance(reader,PSPReader):
			self.reader = reader
			self.linearray = linearray
			self.fileid = fileid
			self.includeStack = []
			self.col = 0
			self.cursor = 0
			self.row = 0
##			return theClass(path=path)
			self.stream = stream
			self.baseDir=inBaseDir
			self.encoding=encoding

		else:
			self = copy.copy(reader)
		
##		I think the includeStack will be copied correctly, but check here for problems
##		raise 'clone include stack'
		

    ## JSP has an equals function, but I don't think I need that, b/c of using copy,
    ## but maybe I do
	
	def getFile(self):
		return self.reader.getFile(self.fileid)

	def __str__(self):
		return self.getFile() + '(' + str(self.line) + str(self.col) + ')'
	
	
	def __repr__(self):
		return self.getFile() + '(' + str(self.col) + ')'	

	def pushStream(self, lines, infileid, inStream, inBaseDir, inEncoding):
		self.includeStack.append((self.cursor, self.row, self.col, self.fileid, self.baseDir, self.encoding, self.stream, self.linearray))

		#print 'cursor on push: ',self.cursor
		self.cursor=0
		self.row=0
		self.col=0
		self.fileid=infileid
		self.baseDir=inBaseDir
		self.encoding=inEncoding
		self.stream=inStream
		self.linearray=lines

	def popStream(self):
		#print 'popping stream: len before pop=',len(self.includeStack)
		if len(self.includeStack) == 0:
			return 0 #false
		list=self.includeStack[len(self.includeStack)-1]
		del self.includeStack[len(self.includeStack)-1]
		self.cursor=list[0]
		self.row=list[1]
		self.col=list[2]
		self.fileid=list[3]
		self.baseDir=list[4]
		self.encoding=list[5]
		self.stream=list[6]
		self.linearray=list[7]
		#print 'cursor on pop:',self.cursor
		return 1 #true
	 




class PSPReader:
    """This class handles the psp source file
    It provides the characters to the other parts of the system.
    It can move forward and backwards in a file and remember locactions"""

    def __init__(self,filename,ctxt):
		self._pspfile = filename
		self._ctxt = ctxt
		self._filehandle = None
		self._lines = []
		self.sourcefiles=[]
		self.current = None
		self.size = 0
		self.master=None

    def init(self):
		self.pushFile(self._ctxt.getFullPspFileName())


    def registerSourceFile(self, file):
		self.sourcefiles.append(file)
		self.size = self.size+1 #what is size for?
		return len(self.sourcefiles)-1

    def pushFile(self, file, encoding=None):
		assert type(file)==type('')
		#if type(file) != type(''): #we've got an open filehandle-don't think this case exists

		#don't know what this master stuff is, but until I do, implement it
		#Oh, it's the original file

		if self.master == None:
			parent = None
			self.master=file
		else:
			parent = os.path.split(self.master)[0]

		isAbsolute = os.path.isabs(file)

		if parent != None and not isAbsolute:
			file = os.path.join(parent,file)


		fileid = self.registerSourceFile(file)
		handle = open(file,'r')
		stream = handle.read()
		handle.seek(0,0)
		lines = handle.readlines() #(self, reader, linearray, fileid, includestack, stream):
		#mark = Mark(self, lines, fileid, None, stream, self._ctxt.getBaseUri(),encoding)

		if self.current == None:
			#self.current = mark
			self.current = mark = Mark(self,lines, fileid, stream, self._ctxt.getBaseUri(),encoding)
		else:
			#raise 'NotImplemented Error'
			self.current.pushStream(lines, fileid, stream, self._ctxt.getBaseUri(), encoding) #don't use yet

    def popFile(self):
		if self.current == None:
			return 0
		self.size = self.size-1 #what the hell is this?
		r=self.current.popStream()

		#print 'popStream returns', r
		return r

    def getFile(self,i):
		return self.sourcefiles[i]

    def newSourceFile(self,filename):
		if filename in self.sourcefiles:
			return None
		sourcefiles.append(filename)
		return len(self.sourcefiles)

    def Mark(self):
		return copy.copy(self.current)
		#return Mark(self.current)

    def advanceLine(self):
		if self.current.row < len(self.current.linearray)-1:
			self.current.cursor = self.current.cursor + len(self.current.linearray[self.current.row][self.current.col:])
			self.current.row = self.current.row + 1
			self.current.col = 0
		else:
			self.current.cursor = self.current.cursor + len(self.current.linearray[self.current.row][self.current.col:])
			self.current.col = len(self.current.linearray[self.current.row][:])
			if self.hasMoreInput() == 0:
				raise EOFError()
    
    def skipUntil(self, st):
		"""greedy search, return after the string"""
		delimlength = len(st)
		pt = 0
		retmark = None

		try:
			while pt == 0:
				pt = string.find(self.current.linearray[self.current.row][self.current.col:],st)
				if pt != -1:
					m = self.Mark()
					m.col = m.col + pt
					m.cursor = m.cursor + pt
					self.current.col = self.current.col + pt + delimlength
					self.current.cursor = self.current.cursor + pt + delimlength
					return m 
				else:
					self.advanceLine()
					pt=0
		except 'EndofInput Error':
			return None

	

    def reset(self, mark):
		self.current = mark #Mark(mark)    

    
    def Matches(self,st):
		if st == self.current.stream[self.current.cursor:self.current.cursor+len(st)]:
			#self.current.cursor = self.current.cursor+len(st)
			#self.current.col = self.current.col + len(st)
			return 1
		return 0

    def Advance(self,length):
		if length + self.current.col <= len(self.current.linearray[self.current.row]):# -1 is to handle '\n'
			self.current.cursor = self.current.cursor + length
			self.current.col = self.current.col + length
			return
			# I may have broken something here. I changed the first line above to <= from < and took out the below 5/20/00
			prog = len(self.current.linearray[self.current.row]) - self.current.col
			# if prog == length:  #I'm gonna have off by 1 errs, try to handle it
			#    self.advanceLine()
			# return
		while prog < length:
			self.advanceLine()
			if prog + len(self.current.linearray[self.current.row]) > length :
				self.current.col = length - prog
				self.current.cursor = self.current.cursor + length - prog
				return
			prog = prog + len(self.current.linearray[self.current.row])

    def nextChar(self):
		if self.hasMoreInput() == 0: return -1
		ch = self.current.stream[self.current.cursor]
	#	self.current.cursor = self.current.cursor + 1
	#	self.current.col = self.current.col + 1
		self.Advance(1)
	#	if self.current.col+1 == len(self.current.linearray[self.current.row]):
	#	    self.current.row = self.current.row + 1
	#	    self.current.col = 0
		return ch

    
    def isSpace(self):
		'''no advancing'''
		return self.current.stream[self.current.cursor] == ' '

    
    def isDelimiter(self):
		if not self.isSpace():
			ch = self.peekChar()
			#look for single character work delimiter
			if ch == '=' or ch == '\"' or ch == "'" or ch == '/':
				return 1
			#look for end of comment or basic end tag
			if ch == '-':
				mark = self.Mark()
				ch = self.nextChar()
				ch2 = self.nextChar()
				if ch == '>' or (ch == '-' and ch2 == '>'):
					self.reset(mark)
					return 1
				else:
					self.reset(mark)
					return 0
		else:
			return 1
		

    

    def peekChar(self,cnt=0):
		#print self.current.cursor,'\n'
		if self.hasMoreInput():
			return self.current.stream[self.current.cursor+cnt]
		raise "EndofStream"

    def skipSpaces(self):
		i = 0
		while self.isSpace():
			self.nextChar()
			i = i+1
		return i

    def getChars(self,start,stop):
		oldcurr = self.Mark()
		self.reset(start)
		chars = self.current.stream[start.cursor:stop.cursor]
		self.reset(oldcurr)
		return chars

    def hasMoreInput(self):
		if self.current.cursor >= len(self.current.stream):
			while self.popFile():
				if self.current.cursor < len(self.current.stream) :
					return 1
			return 0
		return 1

	
    def nextContent(self):
		''' Find next <
		There must be a reason the JSP implementation didnt use skipUntil, but I dont know what it is
		POTENTIAL OFF BY ONE-> might be grabbing the < at the end of the string'''
		cur_cursor = self.current.cursor
		length = len(self.current.stream)
		ch = None

		if self.peekChar()==os.linesep:
			self.current.row = self.current.row + 1
			self.current.col = 0	    
		else:
			self.current.col = self.current.col + 1
		self.current.cursor = self.current.cursor + 1

		while self.current.cursor < length and (self.current.stream[self.current.cursor]) != '<':
			ch = self.current.stream[self.current.cursor]
			if ch == os.linesep:
				self.current.row = self.current.row + 1
				self.current.col = 0
				self.current.cursor = self.current.cursor + 1
			else:
				self.current.cursor = self.current.cursor + 1
				self.current.col = self.current.col+ 1
		return self.current.stream[cur_cursor:self.current.cursor]
    

    def parseTagAttributes(self):
		'''parses the attributes at the beginning of a tag'''

		values = {}
		while 1:
			self.skipSpaces()
			ch = self.peekChar()
			if ch == '>':
				return values
			if ch == '-':
				mark = self.Mark()
				self.nextChar()
				try:
					if self.nextChar() == '-' and self.nextChar() == '>':
						return values
				finally:
					self.reset(mark)
			elif ch == '%':
				mark = self.Mark()
				self.nextChar()
				try:
					ts = self.peekChar()
					if ts == '>':
						self.reset(mark)
						return values
				finally:
					self.reset(mark)

			if ch == None:
				break

			self.parseAttributeValue(values)
		#EOF
		raise 'Unterminated Attribute'

    def parseAttributeValue(self, valuedict):
		self.skipSpaces()
		name = self.parseToken(0)
		self.skipSpaces()
		if self.peekChar() != '=':
			raise 'PSP Error - no attribute value'
		ch = self.nextChar()
		self.skipSpaces()
		value = self.parseToken(1)
		self.skipSpaces()
		valuedict[name]=value

    def parseToken(self, quoted):
		''' This may not be quite right'''
		buffer=[]
		self.skipSpaces()
		ch = self.peekChar()
		if quoted:
			if (ch=='\"' or ch == "\'"):
				endquote = ch
				ch = self.nextChar()
				ch=self.peekChar()
				while ch != None and ch != endquote:
					ch = self.nextChar() 
					if ch == '\\':
						ch = nextChar()
					buffer.append(ch)
					ch = self.peekChar()
				if ch == None:
					raise 'Unterminated Attribute Value'
				self.nextChar()
		else:
			if not self.isDelimiter():
				while not self.isDelimiter():
					ch = self.nextChar()
					if ch == '\\':
						ch = self.peekChar()
						if ch == '\"' or ch == "'" or ch == '>' or ch == '%':
							ch = self.nextChar()
					buffer.append(ch)
		return string.join(buffer,'')
	
			    
		
		
	    

	

    

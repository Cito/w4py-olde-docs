

"""
    This module holds the classes that generate the python code reulting from the PSP template file.
    As the parser encounters PSP elements, it creates a new Generator object for that type of element.
    Each of these elements is put into a list maintained by the ParseEventHandler object.  When it comes
    time to output the Source Code, each generator is called in turn to create it's source.

    
--------------------------------------------------------------------------------
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




import PSPUtils
try:
    import string
except:
    pass

try:
    import os
except:
    pass

#these are global so that the ParseEventHandler and this module agree.
ResponseObject = 'res'
AwakeCreated = 0


class GenericGenerator:
    """ Base class for the generators """
    def __init__(self, ctxt=None):
	self._ctxt = ctxt
	self.phase='Service'


class ExpressionGenerator(GenericGenerator):
    """ This class handles expression blocks.  It simply outputs
    the (hopefully) python expression within the block wrapped
    with a str() call."""

    def __init__(self, chars):
	self.chars = chars
	GenericGenerator.__init__(self)

    def generate(self, writer, phase=None):
	writer.println('res.write(str(' + PSPUtils.removeQuotes(self.chars) + '))')




class CharDataGenerator(GenericGenerator):
    """This class handles standard character output, mostly HTML.  It just dumps it out.
    Need to handle all the escaping of characters.  It's just skipped for now."""

    def __init__(self, chars):
	GenericGenerator.__init__(self)
	self.chars = chars

    def generate(self, writer, phase=None):
	current=0
	limit = len(self.chars)

	#try this without any escaping
	#self.chars = string.replace(self.chars,'\n','\\\\n')
	#self.chars = string.replace(self.chars,'"','\\"')
	#self.chars = string.replace(self.chars,'\t','\\\\t')
	#self.chars = string.replace(self.chars, "'", "\\'")
	
	self.generateChunk(writer)


    def generateChunk(self, writer, start=0, stop=None):
	writer.printIndent()#gives a tab
	writer.printChars(ResponseObject+'.write("""')
	writer.printChars(self.chars)
	writer.printChars('""")')
	writer.printChars('\n')

class ScriptGenerator(GenericGenerator):
    """generates scripts"""
    def __init__(self, chars,attrs):
	GenericGenerator.__init__(self)	
	self.chars = chars

    def generate(self, writer, phase=None):	
	writer.printList(string.splitfields(PSPUtils.removeQuotes(self.chars),'\n'))
	
	writer.printChars('\n')

	#check for a block
	lastline = string.splitfields(PSPUtils.removeQuotes(self.chars),'\n')[-1]
	commentstart = string.find(lastline,'#')
	if commentstart > 0: lastline = lastline[:commentstart]
	blockcheck=string.rstrip(lastline)
	if len(blockcheck)>0 and blockcheck[-1] == ':':
	    writer.pushIndent()
	    writer.println()
	    writer._blockcount = writer._blockcount+1

	#check for end of block, "pass" by itself
	if string.strip(self.chars) == 'pass' and writer._blockcount>0:
	    writer.popIndent()
	    writer.println()
	    writer._blockcount = writer._blockcount-1

class EndBlockGenerator(GenericGenerator):
	def __init__(self):
		GenericGenerator.__init__(self)

	def generate(self, writer, phase=None):
		if writer._blockcount>0:
			writer.popIndent()
			writer.println()
			writer._blockcount = writer._blockcount-1
		
		

class MethodGenerator(GenericGenerator):
    """ generates class methods defined in the PSP page.  There are two parts to method generation.  This
    class handles getting the method name and parameters set up."""
    def __init__(self, chars, attrs):
	GenericGenerator.__init__(self)
	self.phase='Declarations'
	self.attrs=attrs
	
    def generate(self, writer, phase=None):
	writer.printIndent()
	writer.printChars('def ')
	writer.printChars(self.attrs['name'])
	writer.printChars('(')

	#self.attrs['params']
	writer.printChars('self')
	if self.attrs.has_key('params') and self.attrs['params'] != '':
	    writer.printChars(', ')
	    writer.printChars(self.attrs['params'])
	writer.printChars('):\n')
	if self.attrs['name'] == 'awake':  #This is hacky, need better method, but it works: MAybe I should require a standard parent and do the intPSP call in that awake???????
	    AwakeCreated = 1
	    writer.pushIndent()
	    writer.println('self.initPSP()\n')
	    writer.popIndent()
	    writer.println()

class MethodEndGenerator(GenericGenerator):
    """ Part of class method generation.  After MethodGenerator, MethodEndGenerator actually generates
    the code for th method body."""
    def __init__(self, chars, attrs):
	GenericGenerator.__init__(self)
	self.phase='Declarations'
	self.attrs=attrs
	self.chars=chars

    def generate(self, writer, phase=None):
	writer.pushIndent()
	writer.printList(string.splitfields(PSPUtils.removeQuotes(self.chars),'\n'))
       	writer.printChars('\n')
	writer.popIndent()


class IncludeGenerator(GenericGenerator):
    """ Include files designated by the psp:include syntax. Not done yet, just
    a raw dump for now."""
    def __init__(self, attrs, param, ctxt):
	GenericGenerator.__init__(self,ctxt)
	self.attrs = attrs
	self.param = param

	self.page = attrs.get('file')
	if self.page == None:
		raise "No Page attribute in Include"
	thepath=self._ctxt.resolveRelativeURI(self.page)
    
	if not os.path.exists(thepath):
		print self.page
		raise "Invalid included file",thepath
	self.page=thepath

    def generate(self, writer, phase=None):
	""" JSP does this in the servlet.  I'm doing it here because I have triple quotes"""
	data = open(self.page).readlines()
	for i in data:
	    writer.println('res.write("""'+i+'""")\n')
	writer.println()
	
	
	
    
	
	


    

    
    
	

"""
This module handles requests from the application for PSP pages.


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


"""

from ServletFactory import ServletFactory


import string
import os
from PSP import Context, PSPCompiler
import time


class PSPServletFactory(ServletFactory):
	'''
	Servlet Factory for PSP files.
	Very sloppy.  Need to come back and do a serious cleanup.
        
	'''

	def __init__(self,application):
	    ServletFactory.__init__(self,application)

	    self.application = application
	    self.apppath = application.serverDir()
	    self.cacheDir = os.path.join(self.apppath, 'cache')
	    self._classcache={}
	    

	def uniqueness(self):
            return 'file'

	def extensions(self):
            return ['.psp']

	def computeClassName(self,pagename):
	    tail=None
		junk,pagename=os.path.splitdrive(pagename)
	    head,tail = os.path.split(pagename)
	    className = string.replace(tail,'.','_')
	    while head != '/' and head != '':
		head, tail = os.path.split(head)
		className = tail + '_'+ className
	    className=string.replace(className,'.','_')
	    return className

	def createInstanceFromFile(self,filename,classname,mtime):
	    globals={}
	    execfile(filename,globals)
	    assert globals.has_key(classname)
	    instance = globals[classname]()
	    code=globals[classname]
	    self._classcache[classname] = {'code':code,
					   'filename':filename,
					   'mtime':time.time(),}
	    return instance


	def checkClassCache(self, classname, mtime):
	    if self._classcache.has_key(classname) and self._classcache[classname]['mtime'] > mtime:
			return self._classcache[classname]['code']()
	    return None

	
	def servletForTransaction(self, trans):
		fullname = trans.request().serverSidePath()
		path,pagename = os.path.split(fullname)
		mtime = os.path.getmtime(fullname)
	    
		classname = self.computeClassName(fullname)

	    #see if we can just create a new instance
		instance = self.checkClassCache(classname,mtime)
		if instance != None:
			return instance
	    
		cachedfilename = os.path.join(self.cacheDir,str(classname + '.py'))
	    
		if os.path.exists(cachedfilename) and os.stat(cachedfilename)[6] > 0:
			if os.path.getmtime(cachedfilename) > mtime:
				instance = self.createInstanceFromFile(cachedfilename,classname,mtime)
				return instance

		pythonfilename = cachedfilename

		context = Context.PSPCLContext(fullname,trans)
		context.setClassName(classname)
		context.setPythonFileName(pythonfilename)
	

		clc = PSPCompiler.Compiler(context)

		print 'creating python class: ' , classname
		clc.compile()

		instance = self.createInstanceFromFile(cachedfilename,classname,mtime)	    
		return instance




"""
This is a Quick and dirty Kid Template Factory for WebWare.
Basically this allows you to run kid template files directly from
within WebWare without needing to rerun cheetah-compile.  This module
does no caching; the template is rebuilt each time it is requested.
"""
__author__ = 'Winston W (http://stratolab.com)'
__credit__ = 'Copied from a Cheetah servlet factory by: jmquigs@bigfoot.com'


import logging
from WebKit.ServletFactory import ServletFactory
from WebKit.Page import Page

import kid

_log = logging.getLogger(__name__)


class ServletWrapper( Page ):
	'''
	I am a WebKit.Servlet, and when I am asked to respond, I will run the KID template
	to produce the html page.
	'''

	def __init__( self, kidFileName ):
		self._kidModule = kid.load_template( kidFileName, cache=True )
		self._factory = None	# Somebody still uses this, although it seems to be deprecated.

	def respond( self, trans ):
		'''
		I am the main entry point to a Servlet.  I will run the KID template
		and send it's output to the HTTPResponse object.
		'''
		
		httpRequest = trans.request()	# The entire HTTPRequest object, in case the template needs it.
		fields = httpRequest.fields()	# the GET/PUT fields.  This is usually all that is needed.
		httpResponse = trans.response()
		_log.debug('fields=%s', fields )

		template = self._kidModule.write( trans.response(), req=httpRequest, resp=httpResponse, fields=fields)
		
		

class KidServletFactory(ServletFactory):
    def __init__(self,application):
        ServletFactory.__init__(self,application)
        
    def uniqueness(self):
        return 'file'

    def extensions(self):
        return ['.kid']

    def flushCache(self):
        pass
    
    def servletForTransaction(self, trans):
        fullname = trans.request().serverSidePath()
        
        _log.debug('fullname=%s',fullname)

        theServlet = ServletWrapper( fullname )

        return theServlet

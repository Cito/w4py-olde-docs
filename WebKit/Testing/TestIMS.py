from WebKit.Page import Page

class TestIMS(Page):

	def error(self, msg):
		self.write( '<p style="color: red">%s</p>' % self.htmlEncode( msg ) )

	def writemsg( self, msg ):
		self.write( '<p>%s</p>' % self.htmlEncode( msg ) )
		
	def writetest( self, msg ):
		self.write( '<p><b>%s</b></p>' % self.htmlEncode( msg ) )
		
	def getdoc( self, host, path, headers={} ):
		import httplib
		con = httplib.HTTPConnection( host )
		con.request( "GET", path, headers=headers )
		return con.getresponse()

	def writeContent(self):

		adapter = self.request().adapterName()

		self.write("<h1>Test If-Modified-Since support in Webware</h1>")

		# pick a static file which is served up by Webwares UnknownFileHandler
		self.runtest( "%s/PSPExamples/psplogo.png" % adapter )

	def runtest(self, path):
		import time

		host = "localhost"
		
		self.writetest( "Opening %s" % path )

	        rsp = self.getdoc( host, path )
		originalsize = size = len( rsp.read() )
		
		if (rsp.status != 200):
			self.error( "Expected status of 200, received %s" % rsp.status )
			return
		if (size > 0):
			self.writemsg( "Received: %s %s, document size=%s as expected" % (rsp.status, rsp.reason, size ) )
		else:
			self.error( "Document size is: %d" % size )
			return
		lm = rsp.getheader( "Last-Modified", "" )
		if lm:
			self.writemsg( "Last modified: %s" % lm )
		else:
			self.error( "No Last-Modified header found." )
			return

		# Retrieve document again with IMS and expect a 304 not modified
		self.writetest( "Opening %s with If-Modified-Since: %s" % (path, lm ) )
		rsp = self.getdoc( host, path, {'If-Modified-Since' : lm } )
		size = len( rsp.read() )
		if (rsp.status != 304):
			self.error( "Expected status of 304, received %s" % rsp.status )
			return
		if (size):
			self.error( "Expected 0 length document, received %d bytes" % size )
			return
		else:
			self.writemsg( "Received %s %s, document size=%s as expected" % (rsp.status, rsp.reason, size ) )

		
		arpaformat = '%a, %d %b %Y %H:%M:%S GMT'
		t = list(time.strptime(lm, arpaformat))
		t[0] = t[0]-1   # last year
		newlm = time.strftime(arpaformat, time.gmtime(time.mktime(t)))
		self.writetest( "Opening %s with If-Modified-Since: %s" % (path, newlm ) )

		rsp = self.getdoc( host, path, {'If-Modified-Since' : newlm } )
		size = len( rsp.read() )

		lm = rsp.getheader( "Last-Modified", "" )
		self.writemsg( "Last modified: %s" % lm )

		if (rsp.status != 200):
			self.error( "Expected status of 200, received %s %s" % (rsp.status, rsp.reason) )
			return
		if (size != originalsize):
			self.error( "Received: %s %s, document size=%s expected size=%s" %
				    (rsp.status, rsp.reason, size, originalsize ) )
			return
		else:
			self.writemsg( "Received: %s %s, document size=%s as expected" % (rsp.status, rsp.reason, size ) )

		self.writetest( "Passed" )

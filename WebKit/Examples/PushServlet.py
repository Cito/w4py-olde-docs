"""
This is a test servlet for the buffered output streams of the app servers.
This probably won't work with the cgi adapters. At least on apache, the data
doesn't seem to get flushed.
This will not have the expected functionality on Internet Explorer, as it does
not support the x-mixed-replace content type.
"""

from WebKit.Page import Page
from time import sleep
import random

class PushServlet(Page):
	
	boundary = "MyRandomBoundryIsThisStringAndNumber" + str(random.randint(1000,10000000))
	
	def respond(self, transaction):
		self.response().streamOut().autoCommit(1) #this isn't necessary, but it's here as an example
		self.initialHeader()
		for i in range(1,6):
			self.sendBoundary()
			self.sendLF()
			self.writeContent(i)
			self.sendLF()
			self.response().flush()
			sleep(2)
		

	def initialHeader(self):
		self.response().setHeader("Content-type","multipart/x-mixed-replace; boundary=" + self.boundary)

	def sendBoundary(self):
		self.write("--"+self.boundary)

	def sendLF(self):
		self.write("\r\n")
		

	def writeContent(self,count):
		self.write("Content-type: text/html\r\n\r\n")
		self.write("<HTML><BODY><h1 align=center>")
		self.write("Count = %s" % count)
		self.write("</h1></body></html>")

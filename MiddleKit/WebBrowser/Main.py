from SitePage import SitePage
import os, sys
from WebUtils.WebFuncs import HTMLEncode


class Main(SitePage):

	def writeHTML(self):
		self.response().setHeader('Location', 'SelectModel')

from WebKit.SidebarPage import SidebarPage
import string, os


class ExamplePage(SidebarPage):
	'''
	TO DO:
	* Support plug-ins generically.
	'''

	def cornerTitle(self):
		return 'WebKit Examples'

	def isDebugging(self):
		return 0

	def scripts(self):
		''' Create a list of dictionaries, where each dictionary stores information about a particular script. '''
		from stat import *
		import os
		scripts = []
		#dir = self.request().serverSideDir()
		dir = self.request().uriWebKitRoot() + 'Examples'
		examples = eval(open(self.application().serverSidePath('Examples/Examples.list')).read())
		for name in examples:
			script = {}
			script['pathname'] = dir + '/' + name
			script['name']     = name
			scripts.append(script)
		return scripts

	def writeSidebar(self):
		self.startMenu()
		self.writeExamplesMenu()
		self.writeOtherMenu()
		self.writeWebKitSidebarSections()
		self.endMenu()

	def writeExamplesMenu(self):
		self.menuHeading('Examples')
		for script in self.scripts():
			self.menuItem(script['name'], script['pathname'])

	def writeOtherMenu(self):
		self.menuHeading('Other')

		viewPath = self.request().uriWebKitRoot() + "Examples/View"
		self.menuItem(
			'View source of %s' % self.title(),
			self.request().uriWebKitRoot() + 'Examples/View?filename=%s' % string.replace(self.request().serverSidePath(), '\\', '/'))

		if self.application().hasContext('Documentation'):
			filename = 'Documentation/WebKit.html'
			if os.path.exists(filename):
				self.menuItem('Local WebKit docs', self.request().adapterName() + '/' + filename)

from SidebarPage import SidebarPage
import os


class AdminPage(SidebarPage):
	'''
	AdminPage is the abstract superclass of all WebKit administration
	pages.

	Subclasses typically override title() and writeContent(), but may
	customize other methods.
	'''

	def cornerTitle(self):
		return 'WebKit AppServer'

	def writeSidebar(self):
		app = self.application()
		self.startMenu()
		self.writeAdminMenu()
		self.writeWebKitSidebarSections()
		self.endMenu()

	def writeAdminMenu(self):
		self.menuHeading('Admin')
		self.menuItem('Home', '')
		self.menuItem('Activity log', 'Access', self.fileSize('ActivityLogFilename'))
		self.menuItem('Error log', 'Errors', self.fileSize('ErrorLogFilename'))
		self.menuItem('Config', 'Config')
		self.menuItem('Plug-ins', 'PlugIns')
		self.menuItem('Servlet cache by path', 'ServletCacheByPath')
		self.menuItem('Application Control','AppControl')

	def fileSize(self, filename):
		''' Utility method for writeMenu() to get the size of a configuration file. Returns an HTML string. '''
		filename = self.application().setting(filename)
		if os.path.exists(filename):
			return '<font size=-1>(%0.0f KB)</font>' % (os.path.getsize(filename)/1024.0)
		else:
			return '<font size=-1>(does not exist)</font>'

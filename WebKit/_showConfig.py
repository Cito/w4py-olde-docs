from AdminPage import *
import WebUtils.WebFuncs

class _showConfig(AdminPage):

	def title(self):
		return 'Config'

	def writeBody(self):
		self.heading('AppServer')
		self.writeln(WebUtils.WebFuncs.HTMLForDictionary(self.application().server().config()))
		
		self.heading('Application')
		self.writeln(WebUtils.WebFuncs.HTMLForDictionary(self.application().config()))

	def heading(self, heading):
		self.writeln('<p><br><table align=center width=100%% bgcolor=black><tr><td><b><font color=white>%s</font></b></td></tr></table>' % heading)
		
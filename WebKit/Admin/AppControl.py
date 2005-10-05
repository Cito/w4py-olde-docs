from AdminPage import AdminPage
from AdminSecurity import AdminSecurity
import sys


class AppControl(AdminSecurity):

	def writeContent(self):
		req = self.request()
		wr = self.writeln
		action = self.request().field("action",None)

		if action == None:
			if not self.application().server().isPersistent():
				wr('<p><b>You are running the <i>OneShot</i> version of WebKit.'
					' None of the options below are applicable.</b><p>')
			wr('''<form method="post">
<table cellspacing="4" cellpadding="4">
<tr><td><input type="submit" name="action" value="Shutdown"></td>
<td>Shut down the AppServer. You need to restart it manually afterwards.</td>
</tr><tr>
<td><input type="submit" name="action" value="Clear cache"></td>
<td>Clear the class and instance caches of each servlet factory.</td>
</tr><tr>
<td><input type="submit" name="action" value="Reload"></td>
<td>Reload the selected Python modules. Be Careful!</td></tr>''')
			mods = sys.modules.keys()
			mods.sort()
			wr('<tr><td></td><td>')
			for m in mods:
				wr('<input type="checkbox" name="reloads" value="%s">'
					' %s<br>' % (m, m))
			wr('</td></tr>\n</table>\n</form>')

		elif action == "Clear cache":
			from WebKit.URLParser import ServletFactoryManager
			factories = filter(lambda f: f._classCache,
				ServletFactoryManager._factories)
			wr('<p>')
			for factory in factories:
				wr('Flushing cache of %s...<br>' % factory.name())
				factory.flushCache()
			wr('</p>')
			wr('<p style="color:green">The caches of all factories'
				' have been flushed.</p>')
			wr('<p>Click here to view the Servlet cache:'
				' <a href="ServletCache">Servlet Cache</a></p>')

		elif action == "Reload":
			wr('<p>Reloading selected modules. Any existing classes'
				' will continue to use the old module definitions,'
				' as will any functions/variables imported using "from".'
				' Use "Clear Cache" to clean out any servlets'
				' in this condition.<p>')
			reloadnames = req.field("reloads", None)
			if not type(reloadnames) == type([]):
				reloadnames = [reloadnames]
			wr('<p>')
			for m in reloadnames:
				if m and sys.modules.get(m, None):
					wr("Reloading %s...<br>" %
						self.htmlEncode(str(sys.modules[m])))
					try:
						reload(sys.modules[m])
					except Exception, e:
						wr('<span style="color:red">Could not reload,'
							' error was "%s".</span><br>' % e)
			wr('</p>')
			wr('<p style="color:green">The selected modules'
				' have been reloaded.</p>')

		elif action == "Shutdown":
			wr('<p>Shutting down the Application server...</p>')
			self.application().server().initiateShutdown()
			self.write('<p style="color:green"><b>Good Luck!</b></p>')

		else:
			wr('<p>Cannot perform "%s".</p>' % action)


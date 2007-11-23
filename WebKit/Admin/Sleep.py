import os
from time import sleep

from WebKit.Application import ConnectionAbortedError
from AdminSecurity import AdminSecurity


class Sleep(AdminSecurity):

	def title(self):
		return 'Sleep'

	def writeContent(self):
		wr = self.writeln
		field = self.request().field
		try:
			duration = int(field("duration"))
		except (KeyError, ValueError):
			duration = 0
		wr('''<form action="Sleep" method="post">
			<input type="submit" name="action" value="Sleep">
			<input type="text" name="duration" value="%d"
			size="6" maxlength="12" style="text-align: right"> seconds
			</form>''' % (duration or 60))
		if duration:
			wr('<p>Sleeping %d seconds...</p>' % duration)
			self.response().flush(0)
			try:
				for i in xrange(8*duration):
					# Don't block on system call or this thread can't be killed
					sleep(0.125)
				wr('<p>Time over, woke up!</p>')
			except ConnectionAbortedError:
				wr('<p style="color:red">Sleep aborted!</p>')

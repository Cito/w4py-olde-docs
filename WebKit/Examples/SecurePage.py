import string, types
from ExamplePage import ExamplePage

# Set this to 0 if you want to allow everyone to access secure pages with no login
# required.  This should instead come from a config file.
require_login = 1

if not require_login:
	class SecurePage(ExamplePage):
		def writeHTML(self):
			session = self.session()
			request = self.request()
			# Are they logging out?
			if request.hasField('logout'):
				# They are logging out.  Clear all session variables.
				session.values().clear()
			# write the page
			ExamplePage.writeHTML(self)
			
else:
	class SecurePage(ExamplePage):
		def writeHTML(self):
			session = self.session()
			request = self.request()
			trans = self.transaction()
			app = self.application()
			# Get login id and clear it from the session
			loginid = session.value('loginid', None)
			if loginid: session.delValue('loginid')
			# Are they logging out?
			if request.hasField('logout'):
				# They are logging out.  Clear all session variables.
				session.values().clear()
				request.fields()['extra'] = 'You have been logged out.'
				app.forwardRequestFast(trans, 'LoginPage')
			elif request.hasField('login') and request.hasField('username') and request.hasField('password'):
				# They are logging in.  Clear session
				session.values().clear()
				# Check if this is a valid user/password
				username = request.field('username')
				password = request.field('password')
				if self.isValidUserAndPassword(username, password) and request.field('loginid', 'nologin')==loginid:
					# Success; log them in and send the page
					session.setValue('authenticated_user', username)
					ExamplePage.writeHTML(self)
				else:
					# Failed login attempt; have them try again
					request.fields()['extra'] = 'Login failed.  Please try again.'
					app.forwardRequestFast(trans, 'LoginPage')
			# They aren't logging in; are they already logged in?
			elif session.value('authenticated_user', None):
				# They are already logged in; write the HTML for this page.
				ExamplePage.writeHTML(self)
			else:
				# They need to log in.
				session.values().clear()
				app.forwardRequestFast(trans, 'LoginPage')
		
		def isValidUserAndPassword(self, username, password):
			# Replace this with a database lookup, or whatever you're using for
			# authentication...
			users = [('Alice', 'Alice'), ('Bob', 'Bob')]
			return (username, password) in users
	
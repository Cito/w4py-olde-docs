import string, types
from MiscUtils.Configurable import Configurable
from ExamplePage import ExamplePage

class SecurePage(ExamplePage, Configurable):
	'''
	This class is an example of how to implement username and password-based
	security using WebKit.  Use a SecurePage class like this one as the
	base class for any pages that you want to require login.  Modify
	the isUserNameAndPassword method to perform validation in whatever
	way you desire, such as a back-end database lookup.  You might also
	want to modify loginUser so that it automatically brings in additional
	information about the user and stores it in session variables.

	You can turn off security by creating a config file called SecurePage.config
	in the Configs directory with the following contents:

		{
			'RequireLogin': 0
		}

	To-Do: Integrate this functionality with the upcoming UserKit.
	       Make more of the functionality configurable in the config file.

	'''

	def __init__(self):
		ExamplePage.__init__(self)
		Configurable.__init__(self)

	def writeHTML(self):
		# Check the configuration file to see if login is required.
		if self.setting('RequireLogin'):
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
				app.includeURL(trans, 'LoginPage')
			elif request.hasField('login') and request.hasField('username') and request.hasField('password'):
				# They are logging in.  Clear session
				session.values().clear()
				# Check if this is a valid user/password
				username = request.field('username')
				password = request.field('password')
				if self.isValidUserAndPassword(username, password) and request.field('loginid', 'nologin')==loginid:
					# Success; log them in and send the page
					self.loginUser(username)
					ExamplePage.writeHTML(self)
				else:
					# Failed login attempt; have them try again
					request.fields()['extra'] = 'Login failed.  Please try again. (And make sure cookies are enabled.)'
					app.includeURL(trans, 'LoginPage')
			# They aren't logging in; are they already logged in?
			elif self.getLoggedInUser():
				# They are already logged in; write the HTML for this page.
				ExamplePage.writeHTML(self)
			else:
				# They need to log in.
				session.values().clear()
				app.includeURL(trans, 'LoginPage')
		else:
			# No login is required
			session = self.session()
			request = self.request()
			# Are they logging out?
			if request.hasField('logout'):
				# They are logging out.  Clear all session variables.
				session.values().clear()
			# write the page
			ExamplePage.writeHTML(self)

	def isValidUserAndPassword(self, username, password):
		# Replace this with a database lookup, or whatever you're using for
		# authentication...
		users = [('Alice', 'Alice'), ('Bob', 'Bob')]
		return (username, password) in users

	def loginUser(self, username):
		# We mark a user as logged-in by setting a session variable called
		# authenticated_user to the logged-in username.
		#
		# Here, you could also pull in additional information about this user
		# (such as a user ID or user preferences) and store that information
		# in session variables.
		self.session().setValue('authenticated_user', username)

	def getLoggedInUser(self):
		# Gets the name of the logged-in user, or returns None if there is
		# no logged-in user.
		return self.session().value('authenticated_user', None)

	def defaultConfig(self):
		return {'RequireLogin': 1}

	def configFilename(self):
		return 'Configs/SecurePage.config'

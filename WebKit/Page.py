from Common import *
from HTTPServlet import HTTPServlet


class PageError(Exception):
	pass


class Page(HTTPServlet):
	'''
	Page is a type of HTTPServlet that is more convenient for Servlets which represent HTML pages generated in response to GET and POST requests. In fact, this is the most common type of Servlet.
	Subclasses typically override writeHeader(), writeBody() and writeFooter().
	They might also choose to override writeHTML() entirely.
	In awake(), the page sets self attributes, _transaction, _response and _request which subclasses should use as appropriate.
	For the purposes of output, the write() and writeln() convenience methods are provided.
	When developing a full-blown website, it's common to create a subclass of Page called SitePage which defines the common look and feel of the website and provides site-specific convenience methods. Then all other page classes inherit from SitePage.
	'''

	## Transactions ##

	def awake(self, transaction):
		HTTPServlet.awake(self, transaction)
		# @@ 2000-05-08 ce: move these up to Servlet?
		self._transaction  = transaction
		self._response = transaction.response()
		self._request  = transaction.request()
		self._session  = transaction.session()
		assert self._transaction  is not None
		assert self._response is not None
		assert self._request  is not None
		# @@ 2000-05-08 ce: yes/no: assert self._session is not None

	def respondToGet(self, transaction):
		''' Invokes _respond() to handle the transaction. '''
		self._respond(transaction)

	def respondToPost(self, transaction):
		''' Invokes _respond() to handle the transaction. '''
		self._respond(transaction)

	def _respond(self, transaction):
		''' Handles actions if an _action_ field is defined, otherwise invokes writeHTML(). '''
		req = transaction.request()
		if req.hasField('_action_'):
			action = self.methodNameForAction(req.field('_action_'))
			actions = self._actionSet()
			if actions.has_key(action):
				self.preAction(action)
				apply(getattr(self, action), (transaction,))
				self.postAction(action)
			else:
				raise PageError, "Action '%s' is not in the public list of actions, %s." % (action, actions.keys())
		else:
			self.writeHTML()

	def sleep(self, transaction):
		self._session = None
		self._request  = None
		self._response = None
		self._transaction = None
		HTTPServlet.sleep(self, transaction)


	## Access ##

	def application(self):
		return self._transaction.application()

	def transaction(self):
		return self._transaction

	def request(self):
		return self._request

	def response(self):
		return self._response

	def session(self):
		return self._session


	## Generating results ##

	def title(self):
		''' Subclasses often override this method to provide a custom title. This title should be absent of HTML tags. This implementation returns the name of the class, which is sometimes appropriate and at least informative. '''
		return self.__class__.__name__

	def htTitle(self):
		''' Return self.title(). Subclasses sometimes override this to provide an HTML enhanced version of the title. This is the method that should be used when including the page title in the actual page contents. '''
		return self.title()

	def htBodyArgs(self):
		''' The arguments used for the HTML <body> tag. Invoked by writeHeader(). '''
		return 'color=black bgcolor=white'

	def writeHTML(self):
		''' Subclasses may override this method (which is invoked by respondToGet() and respondToPost()) or it's constituent methods, writeHeader(), writeBody() and writeFooter(). '''
		self.writeln('<html>')
		self.writeHeader()
		self.writeBody()
		self.writeFooter()
		self.writeln('</html>')

	def writeHeader(self):
		self.writeln('''<head>
	<title>%s</title>
</head>
<body %s>''' % (self.title(), self.htBodyArgs()))

	def writeBody(self):
		self.writeln("<p>This page has not yet customized it's body.")

	def writeFooter(self):
		self.writeln('</body>')


	## Writing ##

	def write(self, *args):
		for arg in args:
			self._response.write(str(arg))

	def writeln(self, *args):
		for arg in args:
			self._response.write(str(arg))
		self._response.write('\n')


	## Threading ##

	def canBeThreaded(self):
		''' Returns 0 because of the ivars we set up in awake(). '''
		return 0


	## Actions ##

	def methodNameForAction(self, name):
		''' Invoked by _respond() to determine the method name for a given action name (which usually comes from an HTML submit button in a form). This implementation simple returns the name. Subclasses could "filter" the name by altering it or looking it up in a dictionary. Subclasses should override this method with action names don't match their method names. '''
		return name

	def actions(self):
		''' Returns an array of method names that are allowable actions from HTML forms. The default implementation returns []. '''
		return []

	def preAction(self, actionName):
		''' Invoked by self prior to invoking a action method. This implementation basically invokes writeHeader(). Subclasses may override to customize and may or may not invoke super as they see fit. The actionName is passed to this method, although it seems a generally bad idea to rely on this. However, it's still provided just in case you need that hook. '''
		self.writeln('<html>')
		self.writeHeader()

	def postAction(self, actionName):
		''' Invoked by self after invoking a action method. This implementation basically invokes writeFooter(). Subclasses may override to customize and may or may not invoke super as they see fit. The actionName is passed to this method, although it seems a generally bad idea to rely on this. However, it's still provided just in case you need that hook. '''
		self.writeFooter()
		self.writeln('</html>')


	## Self utility ##

	def getCan(self, ID, klass, storage,*args, **kargs):
		"""Gets a Can"""
		storage = string.lower(storage)
		if storage=="session":
			container=self._transaction.session()
		elif storage=="request":
			container=self._transaction.request()
		elif storage=="application":
			container=self._transaction.application()
		else:
			print storage
			raise "Invalid Storage Parameter",storage

		instance = container.getCan(ID)
		if instance == None:
			instance = apply(self._transaction.application()._canFactory.createCan,(klass,)+args,kargs)
			container.setCan(ID,instance)
		return instance


	## Private utility ##

	def _actionSet(self):
		''' Returns a dictionary whose keys are the names returned by actions(). The dictionary is used for a quick set-membership-test in self._respond. Subclasses don't generally override this method or invoke it. '''
		if not hasattr(self, '_actionDict'):
			self._actionDict = {}
			for action in self.actions():
				self._actionDict[action] = 1
		return self._actionDict


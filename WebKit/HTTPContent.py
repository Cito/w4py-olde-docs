from Common import *
from HTTPServlet import HTTPServlet
from WebUtils import Funcs
from Application import EndResponse


class HTTPContentError(Exception):
	pass


class HTTPContent(HTTPServlet):
	"""Content producing HTTP servlet.

	HTTPContent is a type of HTTPServlet that is more convenient for
	Servlets which represent content generated in response to
	GET and POST requests.  If you are generating HTML content, you
	you probably want your servlet to inherit from Page, which contains
	many HTML-related convenience methods.

	If you are generating non-HTML content, it is appropriate to inherit
	from this class directly.

	Subclasses typically override defaultAction().

	In `awake`, the page sets self attributes: `_transaction`,
	`_response` and `_request` which subclasses should use as
	appropriate.

	For the purposes of output, the `write` and `writeln`
	convenience methods are provided.

	If you plan to produce HTML content, you should start by looking
	at Page instead of this lower-level class.

	"""

	## Transactions ##

	def awake(self, transaction):
		"""Let servlet awake.

		Makes instance variables from the transaction. This is
		where Page becomes unthreadsafe, as the page is tied to
		the transaction. This is also what allows us to
		implement functions like `write`, where you don't
		need to pass in the transaction or response.

		"""
		HTTPServlet.awake(self, transaction)
		self._response    = transaction.response()
		self._request     = transaction.request()
		self._session     = None  # don't create unless needed
		assert self._transaction is not None
		assert self._response    is not None
		assert self._request     is not None

	def respondToGet(self, transaction):
		"""Respond to GET.

		Invoked in response to a GET request method. All methods
		are passed to `_respond`.
		"""
		self._respond(transaction)

	def respondToPost(self, transaction):
		"""Respond to POST.

		Invoked in response to a POST request method. All methods
		are passed to `_respond`.

		"""
		self._respond(transaction)

	def _respond(self, transaction):
		"""Respond to action.

		Handles actions if an ``_action_`` or ``_action_XXX``
		field is defined, otherwise invokes `writeHTML`.
		Invoked by both `respondToGet` and `respondToPost`.

		"""
		req = transaction.request()

		# Support old style actions from 0.5.x and below.
		# Use setting OldStyleActions in Application.config
		# to use this.
		if self.transaction().application().setting('OldStyleActions', ) \
				and req.hasField('_action_'):
			action = self.methodNameForAction(req.field('_action_'))
			actions = self._actionSet()
			if actions.has_key(action):
				self.preAction(action)
				apply(getattr(self, action), (transaction,))
				self.postAction(action)
				return
			else:
				raise HTTPContentError, "Action '%s' is not' \
					' in the public list of actions, %s, for %s." \
					% (action, actions.keys(), self)

		# Check for actions
		for action in self.actions():
			if req.hasField('_action_%s' % action) or \
					req.field('_action_', None) == action or \
					(req.hasField('_action_%s.x' % action) and \
					req.hasField('_action_%s.y' % action)):
				self.handleAction(action)
				return

		# If no action was found, run the default.
		self.defaultAction()

	def defaultAction(self):
		"""Default action.

		The core method that gets called as a result of requests.
		Subclasses should override this.

		"""
		pass

	def sleep(self, transaction):
		"""Let servlet speel again.

		:ignore:
		We unset some variables. Very boring.

		"""
		self._session = None
		self._request  = None
		self._response = None
		self._transaction = None
		HTTPServlet.sleep(self, transaction)


	## Access ##

	def application(self):
		"""The `Application` instance we're using."""
		return self._transaction.application()

	def transaction(self):
		"""The `Transaction` we're currently handling."""
		return self._transaction

	def request(self):
		"""The request (`HTTPRequest`) we're handling."""
		return self._request

	def response(self):
		"""The response (`HTTPResponse`) we're handling."""
		return self._response

	def session(self):
		"""The session object.

		This provides a state for the current user
		(associated with a browser instance, really).
		If no session exists, then a session will be created.

		"""
		if not self._session:
			self._session = self._transaction.session()
		return self._session


	## Writing ##

	def write(self, *args):
		"""Write to output.

		Writes the arguments, which are turned to strings (with `str`)
		and concatenated before being written to the response.

		"""
		for arg in args:
			self._response.write(str(arg))

	def writeln(self, *args):
		"""Write to output with newline.

		Writes the arguments (like `write`), adding a newline after.

		"""
		for arg in args:
			self._response.write(str(arg))
		self._response.write('\n')


	## Threading ##

	def canBeThreaded(self):
		"""Declares whether servlet can be threaded.

		Returns 0 because of the instance variables we set up in `awake`.
		"""
		return 0


	## Actions ##

	def handleAction(self, action):
		"""Handle action.

		Invoked by `_respond` when a legitimate action has
		been found in a form. Invokes `preAction`, the actual
		action method and `postAction`.

		Subclasses rarely override this method.

		"""
		self.preAction(action)
		getattr(self, action)()
		self.postAction(action)

	def actions(self):
		"""The allowed actions.

		Returns a list of method names that are allowable
		actions from HTML forms. The default implementation
		returns [].  See `_respond` for more about actions.

		"""
		return []

	def preAction(self, actionName):
		"""Things to do before action.

		Invoked by self prior to invoking a action method.
		The `actionName` is passed to this method,
		although it seems a generally bad idea to rely on
		this. However, it's still provided just in case you
		need that hook.

		By default this does nothing.
		"""
		pass

	def postAction(self, actionName):
		"""Things to do after action.

		Invoked by self after invoking a action method.
		Subclasses may override to
		customize and may or may not invoke super as they see
		fit. The `actionName` is passed to this method,
		although it seems a generally bad idea to rely on
		this. However, it's still provided just in case you
		need that hook.

		By default this does nothing.

		"""
		pass

	def urlEncode(self, s):
		"""Alias for `WebUtils.Funcs.urlEncode`.

		Quotes special characters using the % substitutions.

		"""
		## @@: urllib.quote, or
		return Funcs.urlEncode(s)

	def urlDecode(self, s):
		"""Alias for `WebUtils.Funcs.urlDecode`.

		Turns special % characters into actual characters.

		"""
		return Funcs.urlDecode(s)

	def forward(self, URL, context=None):
		"""Forward request.

		Forwards this request to another servlet.
		See `Application.forward` for details.
		The main difference is that here you don't have
		to pass in the transaction as the first argument.

		"""
		self.application().forward(self.transaction(), URL, context)

	def includeURL(self, URL, context=None):
		"""Include output from other servlet.

		Includes the response of another servlet
		in the current servlet's response.
		See `Application.includeURL` for details.
		The main difference is that here you don't have
		to pass in the transaction as the first argument.

		"""
		self.application().includeURL(self.transaction(), URL, context)

	def callMethodOfServlet(self, URL, method, *args, **kwargs):
		"""Call a method of another servlet.

		See `Application.callMethodOfServlet` for details.
		The main difference is that here you don't have
		to pass in the transaction as the first argument.

		A `context` keyword argument is also possible, even
		though it isn't present in the method signature.

		"""
		return apply(self.application().callMethodOfServlet, (self.transaction(), URL, method) + args, kwargs)

	def endResponse(self):
		"""End response.

		When this method is called during `awake` or
		`respond`, servlet processing will end immediately,
		and the accumulated response will be sent.

		Note that `sleep` will still be called, providing a
		chance to clean up or free any resources.

		"""
		raise EndResponse

	def sendRedirectAndEnd(self, url):
		"""Send redirect and end.

		Sends a redirect back to the client and ends the
		response. This is a very popular pattern.

		"""
		self.response().sendRedirect(url)
		self.endResponse()


	## Utility ##

	def sessionEncode(self, url=None):
		"""Utility function to access `Session.sessionEncode`.

		Takes a url and adds the session ID as a parameter.
		This is for cases where you don't know if the client
		will accepts cookies.

		"""
		if url == None:
			url = self.request().uri()
		return self.session().sessionEncode(url)


	## Private Utility ##

	def _actionSet(self):
		"""Return dictionary for actions.

		Returns a dictionary whose keys are the names returned by actions().
		The dictionary is used for a quick set-membership-test in self._respond.
		Subclasses don't generally override this method or invoke it.

		"""
		if not hasattr(self, '_actionDict'):
			self._actionDict = {}
			for action in self.actions():
				self._actionDict[action] = 1
		return self._actionDict


	## Exception Reports ##

	def writeExceptionReport(self, handler):
		"""Write extra information to the exception report.

		The `handler` argument is the exception handler, and
		information is written there (using `writeTitle`,
		`write`, and `writeln`).  This information is added
		to the exception report.

		See `WebKit.ExceptionHandler` for more information.

		"""
		handler.writeln('''
<p>Servlets can provide debugging information here by overriding <tt>writeExceptionReport()</tt>.</p><p>For example:</p>
<pre>
    exceptionReportAttrs = 'foo bar baz'.split()
    def writeExceptionReport(self, handler):
        handler.writeTitle(self.__class__.__name__)
        handler.writeAttrs(self, self.exceptionReportAttrs)
        handler.write('any string')
</pre>
<p>See WebKit/ExceptionHandler.py for more information.</p>
''')

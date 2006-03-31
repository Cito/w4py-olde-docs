#
# AjaxPage.py
#
# Written by John Dickinson based on ideas from
# Apple developer code (developer.apple.com)
# and Nevow 0.4.1 (www.nevow.org).
# Minor changes by Robert Forkel and Christoph Zwerschke.
#

import StringIO, traceback, time, random

from ExamplePage import ExamplePage as BaseClass

# PyJavascript and quote_js based on ideas from Nevow 0.4.1 (www.nevow.org)

def quote_js(what):
	"""Return quoted JavaScript string corresponding to the Python object."""
	if isinstance(what, bool):
		ret = str(what).lower()
	elif isinstance(what, (int, long, float, PyJavascript)):
		ret = str(what)
	else:
		ret = "'%s'" % str(what).replace('\\', '\\\\').replace('\'', '\\\'').replace('\n', '\\n')
	return ret


class PyJavascript(object):
	"""This class simply tanslates a Python expression into a JavaScript string."""

	def __init__(self, name):
		self.__name = name

	def __getattr__(self, aname):
		return self.__class__('%s.%s'%(self, aname))

	def __str__(self):
		return self.__name

	def __call__(self, *a, **kw):
		args = ','.join([quote_js(i) for i in a])
		kwargs = ','.join(['%s=%s' % (k, quote_js(v)) for k, v in kw.items()])
		if args and kwargs:
			allargs = '%s,%s' % (args, kwargs)
		elif not kwargs:
			allargs = args
		elif not args:
			allargs = kwargs
		return self.__class__('%s(%s)' % (self, allargs))

	def __getitem__(self, index):
		return self.__class__('%s[%s]' % (self, quote_js(index)))

	def __repr__(self):
		return self.__str__()


class AjaxPage(BaseClass):
	"""A superclass for Webware servlets using Ajax techniques.

	AjaxPage can be used to make coding XMLHttpRequest() applications easier.

	Subclasses should override the method ajax_allowed() which returns a list
	of method names. These method names refer to Webware Servlet methods that
	are able to be called by an Ajax-enabled web page. This is very similar
	in functionality to Webware's actions.

	A polling mechanism can be used for long running requests (e.g. generating
	reports) or if you want to send commands to the client without the client
	first triggering an event (e.g. for a chat application). In the first case,
	you should also specify a timeout after which polling shall be used.

	"""

	# Class level variables that can be overridden by servlet instances:
	debug = 0 # set to True if you want to see debugging output
	clientPolling = 1 # set to True if you want to use the polling mechanism
	responseTimeout = 90 # timeout of client waiting for a response in seconds

	# Class level variables to help make client code simpler:
	document = PyJavascript('document')
	setTag = PyJavascript('ajax_setTag')
	setClass = PyJavascript('ajax_setClass')
	setValue = PyJavascript('ajax_setValue')
	setReadonly = PyJavascript('ajax_setReadonly')
	alert = PyJavascript('alert')
	generic_ajax = PyJavascript('generic_ajax')
	generic_ajax_form = PyJavascript('generic_ajax_form')
	this = PyJavascript('this')

	# Response Queue for timed out queries:
	_responseQueue = {}

	def writeJavaScript(self):
		BaseClass.writeJavaScript(self)
		s = '<script type="text/javascript" src="ajaxpage%s.js"></script>'
		self.writeln(s % '')
		if self.clientPolling:
			self.writeln(s % '2')

	def actions(self):
		a = BaseClass.actions(self)
		a.append('ajax_controller')
		if self.clientPolling:
			a.append('ajax_response')
		return a

	def ajax_allowed(self):
		return []

	def ajax_clientPollingInterval(self):
		"""Set the interval for the client polling.

		You should always make it a little random to avoid synchronization.

		"""
		return random.choice(range(3, 8))

	def ajax_response(self):
		"""Return queued Javascript functions to be executed by the client.

		This is polled by the client in random intervals in order to get
		results from long-running queries or push content to the client.

		"""
		if self.clientPolling:
			who = self.session().identifier()
			# Set the timeout until the next time this function is called
			# by the client, using the Javascript wait variable:
			cmd = 'wait=%s;' % self.ajax_clientPollingInterval()
			if self._responseQueue.get(who, []): # add in other commands
				cmd += ';'.join([str(val) for req_number, val in self._responseQueue[who]])
				self._responseQueue[who] = []
			if self.debug:
				self.log("Ajax returns from queue: " + cmd)
			self.write(cmd) # write out at least the wait variable

	def ajax_controller(self):
		"""Execute function f with arguments a on the server side.

		Returns Javascript function to be executed by the client immediately.

		"""
		fields = self.request().fields()
		func = fields.get('f')
		args = fields.get('a', [])
		if type(args) != type([]):
			args = [args]
		req_number = args.pop()
		if self.clientPolling and self.responseTimeout:
			start_time = time.time()
		val = self.alert('There was some problem!')
		if func in self.ajax_allowed():
			try:
				func_obj = getattr(self, func)
			except AttributeError:
				val = self.alert('%s, although an approved function, was not found' % func)
			else:
				try: # pull off sequence number added to "fix" IE
					if self.debug:
						self.log("Ajax call %s(%s)" % (func, args))
					val = str(func_obj(*args))
				except Exception:
					err = StringIO.StringIO()
					traceback.print_exc(file=err)
					e = err.getvalue()
					val = self.alert('%s was called, but encountered an error: %s'%(func,e))
					err.close()
		else:
			val = self.alert('%s is not an approved function' % func)
		if self.clientPolling and self.responseTimeout:
			in_time = time.time() - start_time < self.responseTimeout
		else:
			in_time = 1
		if in_time:
			# If the computation of the function did not last very long,
			# deliver it immediately back to the client with this response:
			if self.debug:
				self.log("Ajax returns immediately: " + str(val))
			self.write(val)
		else:
			# If the client request might have already timed out,
			# put the result in the queue and let client poll it:
			if self.debug:
				self.log("Ajax puts in queue: " + str(val))
			who = self.session().identifier()
			if not self._responseQueue.has_key(who):
				self._responseQueue[who] = [(req_number, val)]
			else:
				self._responseQueue[who].append((req_number, val))

	def ajax_cmdToClient(self, cmd):
		"""Send Javascript commands to the client.

		Client polling must be activitated if you want to use this.

		"""
		if self.clientPolling:
			who = self.session().identifier()
			if not self._responseQueue.has_key(who):
				self._responseQueue[who] = []
			self._responseQueue[who].append((None, cmd))

	def preAction(self, action_name):
		if action_name.startswith('ajax_'):
			pass
		else:
			BaseClass.preAction(self, action_name)

	def postAction(self, action_name):
		if action_name.startswith('ajax_'):
			pass
		else:
			BaseClass.postAction(self,action_name)

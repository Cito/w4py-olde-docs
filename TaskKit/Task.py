class Task:

	def __init__(self):
		''' Subclasses should invoke super for this method. '''
		# Nothing for now, but we might do something in the future.
		pass

	def run(self):
		raise SubclassResponsibilityError

	def handle(self):
		return self._handle

	def proceed(self):
		"""
		Should this task continue running?
		Should be called periodically by long tasks to check if the system wants them to exit.
		returns 1 if its OK to continue, 0 if its time to quit
		"""
		return (not self._close.isSet()) and  self._handle._isRunning

	def _run(self, handle):
		self._name = handle.name()
		self._handle = handle
		self._close = handle.closeEvent()
		self.run()
		handle.notifyCompletion()

	def name(self):
		return self._name

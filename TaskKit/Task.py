class Task:

	def __init__(self):
		''' Subclasses should invoke super for this method. '''
		# Nothing for now, but we might do something in the future.
		pass

	def run(self):
		'''
		Override this method for you own tasks. Long running tasks can periodically 
		use the close() Event or the proceed() method to check if a task should stop. 
		If you use close() then single task termination requests will be ignored. 
		With proceed() you also take into account that somebody wants to stop a
		specific task. In case of doubt use proceed().
		'''
		raise SubclassResponsibilityError
	
		
	## Utility method ##	
	
	def proceed(self):
		"""
		Should this task continue running?
		Should be called periodically by long tasks to check if the system wants them to exit.
		Returns 1 if its OK to continue, 0 if its time to quit
		"""
		return (not self._close.isSet()) and  self._handle._isRunning
		
		
	## Attributes ##
	
	def handle(self):
		'''
		A task is scheduled by wrapping a handler around it. It knows
		everything about the scheduling (periodicity and the like).
		Under normal circumstances you should not need the handler,
		but if you want to write period modifying run() methods, 
		it is useful to have access to the handler. Use it with care.
		'''
		return self._handle

	def name(self):
		'''
		Returns the unique name under which the task was scheduled.
		'''
		return self._name

	def close(self):
		'''
		The close Event is set when the scheduler stops. It can be used
		in the run() method to check if a task should terminate too.
		'''
		return self._close	
			

	## Private method ##

	def _run(self, handle):
		'''
		This is the actual run method for the Task thread. It is a private method which
		should not be overriden.
		'''
		self._name = handle.name()
		self._handle = handle
		self._close = handle.closeEvent()
		self.run()
		handle.notifyCompletion()

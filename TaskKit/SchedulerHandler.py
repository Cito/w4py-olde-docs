from time import time, sleep
from threading import Event, Thread


class SchedulerHandler:


	## Init ##

	def __init__(self, scheduler, start, period, task, name):
		self._scheduler = scheduler
		self._task = task
		self._name = name
		self._thread = None
		self._isRunning = 0
		self._suspend = 0
		self._lastTime = None
		self._startTime = start
		self._registerTime = time()
		self._reregister = 1
		self._rerun = 0
		self._period = abs(period)
		self._stopEvent = Event()

	def reset(self, start, period, task, reregister):
		self._startTime = start
		self._period = abs(period)
		self._task = task
		self._reregister = reregister

	def runTask(self):
		if self._suspend:
			self._scheduler.notifyCompletion(self)
			return
		self._rerurn = 0
		self._thread = Thread(None, self._task._run, self.name(), (self,))
		self._thread.start()
		self._isRunning = 1

	def reschedule(self):
		if self._period == 0:
			return 0
		else:
			if self._lastTime - self._startTime > self._period:  #if the time taken to run the task exceeds the period
				self._startTime = self._lastTime + self._period
			else:
				self._startTime = self._startTime + self._period
			return 1

	def runAgain(self):
		return self._rerun

	def isOnDemand(self):
		return self._period == 1

	def runOnCompletion(self):
		self._rerun = 1

	def unregister(self):
		self._reregister = 0
		self._rerun = 0

	def disable(self):
		self._suspend = 1

	def enable(self):
		self._suspend = 0

	def period(self):
		return self._period

	def setPeriod(self, period):
		self._period = period

	def notifyCompletion(self):
		self._isRunning = 0
		self._lastTime = time()
		self._scheduler.notifyCompletion(self)

	def stop(self):
		self._isRunning = 0

	def name(self):
		return self._name

	def closeEvent(self):
		return self._scheduler.closeEvent()

	def startTime(self, newTime=None):
		if newTime:
			self._startTime = newTime
		return self._startTime

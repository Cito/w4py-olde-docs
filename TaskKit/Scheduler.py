from threading import Thread, Event
from SchedulerHandler import SchedulerHandler
from time import time, sleep
from exceptions import IOError

class Scheduler(Thread):


	## Init ##

	def __init__(self):
		Thread.__init__(self)
		self._closeEvent = Event()
		self._notifyEvent = Event()
		self._nextTime = None
		self._scheduled = {}
		self._running = {}
		self._onDemand = {}
		self._isRunning = 0


	## Event Methods ##

	def closeEvent(self):
		"""
		The close event is a scheduling mechanism
		This function returns the close event.
		"""
		return self._closeEvent

	def wait(self, seconds=None):
		"""
		Our own version of wait.
		When called, it waits for the specified number of seconds, or until it is
		notified that it needs to wake up, through the notify event.
		"""
		try:
			self._notifyEvent.wait(seconds)
		except IOError, e:
			pass
		self._notifyEvent.clear()


	## Value Methods ##

	def running(self, name, default=None):
		return self._running.get(name, default)

	def hasRunning(self, name):
		return self._running.has_key(name)

	def setRunning(self, handle):
		self._running[handle.name()] = handle

	def delRunning(self, name):
		try:
			handle = self._running[name]
			del self._running[name]
			return handle
		except:
			return None

	def scheduled(self, name, default=None):
		return self._scheduled.get(name, default)

	def hasScheduled(self, name):
		return self._scheduled.has_key(name)

	def setScheduled(self, handle):
		self._scheduled[handle.name()] = handle

	def delScheduled(self, name):
		try:
			handle = self._scheduled[name]
			del self._scheduled[name]
			return handle
		except:
			return None

	def onDemand(self, name, default=None):
		return self._onDemand.get(name, default)

	def hasOnDemand(self, name):
		return self._onDemand.has_key(name)

	def setOnDemand(self, handle):
		self._onDemand[handle.name()] = handle

	def delOnDemand(self, name):
		try:
			handle = self._onDemand[name]
			del self._onDemand[name]
			return handle
		except:
			return None

	def nextTime(self):
		return self._nextTime

	def setNextTime(self, time):
		self._nextTime = time

	def isRunning(self):
		return self._isRunning


	## Adding Tasks ##

	def addTimedAction(self, time, task, name):
		handle = self.unregisterTask(name)
		if not handle:
			handle = SchedulerHandler(self, time, 0, task, name)
		else:
			handle.reset(time, 0, task, 1)
		self.scheduleTask(handle)

	def addActionOnDemand(self, task, name):
		handle = self.unregisterTask(name)
		if not handle:
			handle = SchedulerHandler(self, time(), 0, task, name)
		else:
			handle.reset(time(), 0, task, 1)
		self.setOnDemand(handle)

	def addDailyAction(self, hour, minute, task, name):
		"""
		Can we make this addCalendarAction?  What if we want to run something once a week?
		We probably don't need that for Webware, but this is a more generally useful module.
		This could be a difficult function, though.  Particularly without mxDateTime.
		"""
		import time
		current = time.localtime(time.time())
		currhour = current[3]
		currmin = current[4]

		#minute_difference
		if minute > currmin:
			minute_difference = minute - currmin
		elif minute < currmin:
			minute_difference = 60 - currmin + minute
		else: #equal
			minute_difference = 0

		#hour_difference
		if hour > currhour:
			hour_difference = hour - currhour
		elif hour < currhour:
			hour_difference = 24 - currhour + hour
		else: #equal
			hour_difference = 0

		delay = (minute_difference + (hour_difference * 60)) * 60

		print "daily task %s scheduled for %s seconds" % (name,delay)

		self.addPeriodicAction(time.time()+delay, 24*60*60, task, name)


	def addPeriodicAction(self, start, period, task, name):
		handle = self.unregisterTask(name)
		if not handle:
			handle = SchedulerHandler(self, start, period, task, name)
		else:
			handle.reset(start, period, task, 1)
		self.scheduleTask(handle)


	## Task methods ##

	def unregisterTask(self, name):
		handle = None
		if self.hasScheduled(name):
			handle = self.delScheduled(name)
		if self.hasOnDemand(name):
			handle = self.delOnDemand(name)
		if handle:
			handle.unregister()
		return handle

	def runTaskNow(self, name):
		if self.hasRunning(name):
			return 1
		handle = self.scheduled(name)
		if not handle:
			handle = self.onDemand(name)
		if not handle:
			return 0
		self.runTask(handle)
		return 1

	def demandTask(self, name): pass

	def stopTask(self, name):
		handle = self.running(name)
		if not handle: return 0
		handle.stop()
		return 1

	def disableTask(self, name):
		handle = self.running(name)
		if not handle:
			handle = self.scheduled(name)
		if not handle:
			return 0
		handle.disable()
		return 1

	def enableTask(self, name):
		handle = self.running(name)
		if not handle:
			handle = self.scheduled(name)
		if not handle:
			return 0
		handle.enable()
		return 1

	def runTask(self, handle):
		name = handle.name()
		if self.delScheduled(name) or self.delOnDemand(name):
			self.setRunning(handle)
			handle.runTask()

	def scheduleTask(self, handle):
		self.setScheduled(handle)
		if not self.nextTime() or handle.startTime() < self.nextTime():
			self.setNextTime(handle.startTime())
			self.notify()


	## Misc Methods ##

	def notifyCompletion(self, handle):
		name = handle.name()
		if self.hasRunning(name):
			self.delRunning(name)
			if handle.startTime() and handle.startTime() > time():
				self.scheduleTask(handle)
			else:
				if handle.reschedule():
					self.scheduleTask(handle)
				elif not handle.startTime():
					self.setOnDemand(handle)
					if handle.runAgain():
						self.runTask(handle)

	def notify(self):
		self._notifyEvent.set()

	def stop(self):
		self._isRunning = 0
		self.notify()
		self._closeEvent.set()


	## Main Method ##

	def run(self):
		self._isRunning = 1
		while 1:
			if not self._isRunning:
				return
			if not self.nextTime():
				self.wait()
			else:
				nextTime = self.nextTime()
				currentTime = time()
				if currentTime < nextTime:
					sleepTime = nextTime - currentTime
					self.wait(sleepTime)
				currentTime = time()
				if currentTime >= nextTime:
					toRun = []
					nextRun = None
					for handle in self._scheduled.values():
						startTime = handle.startTime()
						if startTime <= currentTime:
							toRun.append(handle)
						else:
							if not nextRun:
								nextRun = startTime
							elif startTime < nextRun:
								nextRun = startTime
					self.setNextTime(nextRun)
					for handle in toRun:
						self.runTask(handle)

import os, sys
sys.path.insert(1, os.path.abspath('../..'))
import TaskKit

from TaskKit.Scheduler import Scheduler
from TaskKit.Task import Task
from time import time, sleep


class SimpleTask(Task):

	def run(self, close):
		if self.proceed():
			print self.name(), time()
			#sleep(4)
##			print "Increasing period"
##			self.handle().setPeriod(self.handle().period()+2)
		else:
			print "Should not proceed"


def main():
	from time import localtime
	scheduler = Scheduler()
	scheduler.start()
	scheduler.addPeriodicAction(time(), 2, SimpleTask(), 'SimpleTask1')
	scheduler.addTimedAction(time()+5, SimpleTask(), 'SimpleTask2')
	scheduler.addActionOnDemand(SimpleTask(), 'SimpleTask3')
	scheduler.addDailyAction(localtime(time())[3], localtime(time())[4]+1, SimpleTask(), "DailyTask")
	sleep(30)
	print "Demanding SimpleTask3"
	scheduler.runTaskNow('SimpleTask3')
	sleep(1)
	print "Calling stop"
	scheduler.stop()
	print "Test Complete"


if __name__=='__main__':
	main()

from ExamplePage import ExamplePage
from time import *


class Time(ExamplePage):
	
	def writeBody(self):
		self.write('<p>', asctime(localtime(time())))

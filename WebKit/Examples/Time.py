from ExamplePage import ExamplePage
from time import *


class Time(ExamplePage):

	def writeContent(self):
		self.write('<p>', asctime(localtime(time())))

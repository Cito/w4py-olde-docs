import sys
sys.path.insert(1, '..')
import string
from Funcs import *


def TestCommas():
	testSpec = '''
		0 '0'
		0.0 '0.0'
		1 '1'
		11 '11'
		111 '111'
		1111 '1,111'
		11111 '11,111'
		1.0 '1.0'
		11.0 '11.0'
		1.15 '1.15'
		12345.127 '12,345.127'
	'''
	tests = string.split(testSpec)
	count = len(tests)
	i = 0
	while i<count:
		source = eval(tests[i])
		result = eval(tests[i+1])
		#print '%r yields %r' % (source, result)
		assert commas(source)==result

		# Now try the source as a string instead of a number:
		source = eval("'%s'" % tests[i])
		#print '%r yields %r' % (source, result)
		assert commas(source)==result

		i = i+2


def Test():
	TestCommas()


if __name__=='__main__':
	Test()

'''
Funcs.py

Funcs.py, a member of MiscUtils, holds functions that don't fit in anywhere else.
'''


def Commas(number):
	''' Returns the given number as a string with commas to separate the thousands positions. The number can be a float, int, long or string. Returns None for None. '''
	if number is None:
		return None
	if not number:
		return str(number)
	number = list(str(number))
	if '.' in number:
		i = number.index('.')
	else:
		i = len(number)
	while 1:
		i -= 3
		if i<=0:
			break
		number[i:i] = [',']
	return ''.join(number)

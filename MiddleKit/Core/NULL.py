'''
NULL.py

Defines NULL, an object whose repr() (and therefore str()) is 'NULL'
and NoneToNULL().
'''


class NULL:
	''' NULL is immediately replaced with an instance of itself. It is used to convert Python's None to SQL's NULL when constructing SQL statements. '''
	def __repr__(self):
		return 'NULL'
NULL = NULL()


def NoneToNULL(sequence):
	''' Returns a list that matches a given sequence except with None replaced by NULL. '''
	return [
		(x is None and NULL) or x
			for x in sequence]

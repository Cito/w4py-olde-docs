import types

import sys
sys.path.insert(1, '..')
from Error import Error


def test():
	err = Error(None, None)
	print err
	print repr(err)
	assert err.object() is None
	assert err.message() is None
	print

	err = Error(test, 'test')
	print err
	print repr(err)
	assert err.object() is test
	assert err.message()=='test'
	print

	err = Error(None, '', a=5, b='.')
	print err
	print repr(err)
	assert err.keys() in [['a', 'b'], ['b', 'a']]
	assert type(err['a']) is types.IntType
	assert type(err['b']) is types.StringType
	print


if __name__=='__main__':
	test()

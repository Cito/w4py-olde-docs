class NoException(Exception):
	pass
	
	
def test():
	from Foo import Foo
	from MiddleKit.Run.ObjectStore import Store as store

	f = Foo()
	
	# Test defaults
	assert f.b()==1
	assert f.i()==2
	assert f.l()==3
	assert f.f()==4
	assert f.s()=='5'

	# Test min max
	# These should pass
	for x in range(10):
		f.setI(int(x))
		f.setL(long(x))
		f.setF(float(x))
	for x in range(6):
		s = '.'*(x+5)
		f.setS(s)
		
	# Test min max
	# These should throw exceptions
	if 0:
		for x in [-1, 11]:
			try:		f.setI(int(x))
			except:		pass
			else:		raise NoException

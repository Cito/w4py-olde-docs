def test():
	from Foo import Foo
	from Bar import Bar
	from MiddleKit.Run.ObjectStore import Store as store
	
	bar = store.fetchObjectsOfClass(Bar)[0]
	store.dumpKlassIds()
	assert bar.foo().x()==1
	
	foo = store.fetchObjectsOfClass(Foo)[0]
	assert foo==bar.foo()
	
	
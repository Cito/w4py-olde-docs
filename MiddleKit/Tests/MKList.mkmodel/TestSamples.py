def test():
	from Foo import Foo
	from Bar import Bar
	from MiddleKit.Run.ObjectStore import Store as store

	foos = store.fetchObjectsOfClass(Foo)
	assert len(foos)==2
	f1, f2 = foos
	assert len(f1.bars())==2
	assert len(f2.bars())==3
	

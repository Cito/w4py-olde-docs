def test():
	from Foo import Foo
	from MiddleKit.Run.ObjectStore import Store as store

	a100 = 'a'*100
	b500 = 'b'*500
	c70000 = 'c'*70000

	f = Foo()
	f.setMax100(a100)
	f.setMax500(b500)
	f.setMax70000(c70000)
	store.addObject(f)
	store.saveChanges()

	store.clear()
	results = store.fetchObjectsOfClass(Foo)
	f = results[0]
	assert f.max100()==a100
	assert f.max500()==b500
	assert f.max70000()==c70000

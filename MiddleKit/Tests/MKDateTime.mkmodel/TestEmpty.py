from Foo import Foo
from MiddleKit.Run.ObjectStore import Store as store


def test():
	try:
		from mx import DateTime
		testObjects()
	except ImportError:
		testStrings()
		testNone()


def testStrings():
	print 'Testing with strings.'

	f = Foo()
	f.setD('2001-06-07')
	f.setT('12:42')
	f.setDt('2001-06-07 12:42')

	storeFoo(f)

	f.setD('2002-11-11')
	f.setT('16:04')
	f.setDt('2002-11-11 16:04')

	store.saveChanges()


def testObjects():
	import mx
	from mx.DateTime import DateTimeFrom, TimeFrom
	print 'Testing with DateTime module.'

	d  = DateTimeFrom('2001-06-07')
	t  = TimeFrom('12:42')
	dt = DateTimeFrom('2001-06-07 12:42')

	f = Foo()
	f.setD(d)
	f.setT(t)
	f.setDt(dt)

	storeFoo(f)

	d  = DateTimeFrom('2002-11-11')
	t  = TimeFrom('16:04')
	dt = DateTimeFrom('2002-11-11 16:04')

	f.setD(d)
	f.setT(t)
	f.setDt(dt)

	store.saveChanges()


def storeFoo(f):
	store.addObject(f)
	store.saveChanges()

	store.clear()

	results = store.fetchObjectsOfClass(Foo)
	assert len(results)==1
#	results[0].dumpAttrs()


def testNone():
	print 'Testing None.'

	store.executeSQL('delete from Foo;')

	f = Foo()
	f.setD(None)
	f.setT(None)
	f.setDt(None)

	store.addObject(f)
	store.saveChanges()
	store.clear()

	results = store.fetchObjectsOfClass(Foo)
	assert len(results)==1
	f = results[0]
	assert f.d() is None
	assert f.t() is None
	assert f.dt() is None

def test():
	import os

	from One import One
	from Two import Two

	from MiddleKit.Run.ObjectStore import Store as store

	# Note: Two inherits One

	# Simple creation and insertion
	one = One()
	one.setA('a')
	one.setB('b')
	store.addObject(one)

	two = Two()
	two.setA('1')
	two.setB('2')
	two.setC('3')
	two.setD('4')
	store.addObject(two)

	store.saveChanges()
	store.clear()

	# Fetching
	objs = store.fetchObjectsOfClass(One)
	assert len(objs)==2
	obj = objs[0]
	assert obj.a()=='a'
	assert obj.b()=='b'

	objs = store.fetchObjectsOfClass(One, isDeep=0)
	assert len(objs)==1

	objs = store.fetchObjectsOfClass(One, clauses='where a="1"')
	assert len(objs)==1
	assert objs[0].c()=='3'

	objs = store.fetchObjectsOfClass(One, clauses='where a="2"')
	assert len(objs)==0

	objs = store.fetchObjectsOfClass(Two)
	assert len(objs)==1
	obj = objs[0]
	assert obj.a()=='1'
	assert obj.b()=='2'
	assert obj.c()=='3'
	assert obj.d()=='4'

	# Using fetchObject to fetch individual objects of both base class and subclass
	objs = store.fetchObjectsOfClass(One)
	assert len(objs)==2
	for obj in objs:
		fetchedObj = store.fetchObject(obj.__class__, obj.serialNum())	
		assert fetchedObj.__class__ == obj.__class__
		assert fetchedObj.a() == obj.a()

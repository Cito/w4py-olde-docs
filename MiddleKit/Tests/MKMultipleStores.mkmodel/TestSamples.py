def test():
	from Thing import Thing
	from MiddleKit.Run.ObjectStore import Store as store

	things = store.fetchObjectsOfClass('Thing')
	assert len(things)>1  # make sure have at least some data to work with
	for thing in things:
		assert thing.store()==store

	dbArgs = store._dbArgs
	newStore = store.__class__(**dbArgs)
	newStore.setModel(store.model())
	assert newStore!=store  # paranoia

	things = newStore.fetchObjectsOfClass('Thing')
	assert len(things)>1
	for thing in things:
		assert thing.store()==newStore

	
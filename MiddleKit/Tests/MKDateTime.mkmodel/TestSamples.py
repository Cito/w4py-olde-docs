def test(store):
	from Foo import Foo

	f = store.fetchObjectsOfClass(Foo)[0]

	d  = '2000-01-01'
	t  = '13:01'
	dt = '2000-01-01 13:01'
	try:
		from mx.DateTime import DateTimeFrom, DateTimeDeltaFrom
		print 'Testing with DateTime module.'
		d  = DateTimeFrom(d)
		t  = DateTimeDeltaFrom(t)
		dt = DateTimeFrom(dt)
	except ImportError:
		print 'Testing with strings.'

	from MiddleKit.Design.PythonGenerator import nativeDateTime, mxDateTime

	value = f.d()
	match = False
	if nativeDateTime:
		match = value==nativeDateTime.date(2000, 1, 1)
	if not match and mxDateTime:
		match = value==mxDateTime.DateTime(2000, 1, 1)
	assert match, value

	value = f.t()
	match = False
	if nativeDateTime:
		match = value==store.filterDateTimeDelta(nativeDateTime.time(13, 01))
	if not match and mxDateTime:
		match = value==mxDateTime.DateTimeDeltaFrom('13:01')
	assert match, value

	value = f.dt()
	match = False
	if nativeDateTime:
		match = value==nativeDateTime.datetime(2000, 1, 1, 13, 1)
	if not match and mxDateTime:
		match = value==mxDateTime.DateTime(2000, 1, 1, 13, 1)
	assert match, value

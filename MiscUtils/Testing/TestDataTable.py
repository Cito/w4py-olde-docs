import sys
sys.path.insert(0, '..')
from DataTable import *
import string


def heading(title):
	print
	print title


def test01():
	print 'Simple tests...'

	heading('Create table:')
	t = DataTable()

	heading('Headings 1:')
	t = DataTable()
	t.setHeadings([TableColumn('name'), TableColumn('age:int'), TableColumn('rating:float')])

	heading('Headings 2:')
	t = DataTable()
	t.setHeadings(['name', 'age:int', 'rating:float'])

	heading('Adding and accessing data:')
	a = ['John', '26', '7.2']
	b = ['Mary', 32, 8.3]
	t.append(a)
	t.append(b)
	assert t[-1].asList()==b
	assert t[-2].asDict()=={'name':'John', 'age':26, 'rating':7.2}
	assert t[-1]['name']=='Mary'
	assert t[-2]['name']=='John'

	heading('Printing:')
	print t

	heading('Writing file (CSV):')
	t.writeFile(sys.stdout)

	heading('Accessing rows:')
	for row in t:
		assert row['name']==row[0]
		assert row['age']==row[1]
		assert row['rating']==row[2]
		for item in row:
			pass

	heading('Default type:')
	t = DataTable(defaultType='int')
	t.setHeadings(list('xyz'))
	t.append([1, 2, 3])
	t.append([4, 5, 6])
	assert t[0]['x'] - t[1]['z'] == -5

	heading('Quoted values:')
	t = DataTable()
	# "x",'y,y',z # to do
	lines = split('''x,y,z
		a,b,c
		a,b,"c,d"
		"a,b",c,d
		"a","b","c"
		"a",b,"c"
		"a,b,c"
		"","",""
		"a","",
''', '\n')

	t.readLines(lines)
	assert t.headings()[0].name()=='x'
	assert t.headings()[1].name()=='y'
	assert t.headings()[2].name()=='z'

	matches = [
		['a', 'b', 'c'],
		['a', 'b', 'c,d'],
		['a,b', 'c', 'd'],
		['a', 'b', 'c'],
		['a', 'b', 'c'],
		['a,b,c', '', ''],
		['', '', ''],
		['a', '', '']
	]
	i = 0
	while i<len(t):
		match = matches[i]
		if t[i].asList()!=match:
			print 'mismatch'
			print 'i     :', i
			print 'match :', match
			print 't[i]  :', t[i]
			raise AssertionError
		i = i + 1

	print


def test():
	print 'Testing DataTable.py'
	test01()
	print 'Done.'


if __name__=='__main__':
	test()

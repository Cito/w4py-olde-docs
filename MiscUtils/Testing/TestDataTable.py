import sys
sys.path.insert(0, '..')
from DataTable import *
import string
from string import ljust


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

	heading('Adding data:')
	t.append(['John', '26', '7.2'])
	t.append(['Mary', 32, 8.3])

	heading('Printing:')
	print t

	heading('Writing file (CSV):')
	t.writeFile(sys.stdout)

	heading('Accessing rows:')
	for row in t:
		print row['name'], row['age'], row['rating']
		print row[0], row[1], row[2]
		for item in row:
			print item,
		print

	heading('Default type:')
	t = DataTable(defaultType='int')
	t.setHeadings(list('xyz'))
	t.append([1, 2, 3])
	t.append([4, 5, 6])
	print '<assert>'
	assert t[0]['x'] - t[1]['z'] == -5

	heading('Quoted values:')
	t = DataTable()
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

	# clean up lines for printing and comparison to table
	lines = lines[1:]  # strip heading line (x,y,z)
	lines = map(strip, lines)
	maxLen = 0
	for line in lines:
		if maxLen<len(line):
			maxLen = len(line)
	lines = map(lambda line, ljust=ljust, maxLen=maxLen: ljust(line, maxLen), lines)

	# print lines and table for visual inspection
	for i in range(len(t)):
		print '%02i. %s ==> %s' % (i, lines[i], t[i])
	print


def test():
	print 'Testing DataTable.py'
	test01()
	print 'Done.'


if __name__=='__main__':
	test()

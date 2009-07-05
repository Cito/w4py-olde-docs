import os
import unittest

import FixPath
from MiscUtils import StringIO
from MiscUtils.DataTable import (DataTable, DataTableError,
    TableColumn, TableRecord)


class TestTableColumn(unittest.TestCase):

    def testWithType(self):
        tc = TableColumn('foo:int')
        assert tc.name() == 'foo'
        assert tc.type() is int

    def testWithoutType(self):
        tc = TableColumn('bar')
        assert tc.name() == 'bar'
        assert tc.type() is None

    def testWrongSpec(self):
        self.assertRaises(DataTableError, TableColumn, 'foo:bar')
        self.assertRaises(DataTableError, TableColumn, 'foo:bar:baz')

    def testValueForRawValue(self):
        tc = TableColumn('foo:int')
        assert tc.valueForRawValue('') == 0
        assert tc.valueForRawValue('1') == 1
        assert tc.valueForRawValue(2) == 2
        assert tc.valueForRawValue(2.5) == 2
        tc = TableColumn('bar:str')
        assert tc.valueForRawValue('') == ''
        assert tc.valueForRawValue('1') == '1'
        assert tc.valueForRawValue(2) == '2'
        assert tc.valueForRawValue('x') == 'x'
        tc = TableColumn('bar:float')
        assert tc.valueForRawValue('') == 0.0
        assert tc.valueForRawValue('1') == 1.0
        assert tc.valueForRawValue('1.5') == 1.5
        assert tc.valueForRawValue(2.5) == 2.5
        assert tc.valueForRawValue(3) == 3.0


class Record(object):

    def __init__(self, **record):
        self.record = record

    def hasValueForKey(self, key):
        return key in self.record

    def valueForKey(self, key, default=None):
        return self.record.get(key, default)


class TestDataTable(unittest.TestCase):

    def _testSource(self, name, src, headings, data):
        # print name
        dt = DataTable()
        lines = src.splitlines()
        dt.readLines(lines)
        assert [col.name() for col in dt.headings()] == headings
        for i, values in enumerate(dt):
            match = data[i]
            self.assertEqual(values.asList(), match,
                'For element %d, I expected "%s" but got "%s"'
                % (i, match, values.asList()))

    def testBasicWithPickle(self):
        DataTable.usePickleCache = True
        self._testBasic()
        self._testBasic()

    def testBasicWithoutPickle(self):
        DataTable.usePickleCache = False
        self._testBasic()

    def _testBasic(self):
        """Simple tests..."""

        # Create table
        t = DataTable()

        # Headings 1
        t = DataTable()
        t.setHeadings([TableColumn('name'), TableColumn('age:int'),
            TableColumn('rating:float')])

        # Headings 2
        t = DataTable()
        t.setHeadings(['name', 'age:int', 'rating:float'])

        # Adding and accessing data
        a = ['John', '26', '7.25']
        b = ['Mary', 32, 8.5]
        c = dict(name='Fred', age=28, rating=9.0)
        d = Record(name='Wilma', age=27, rating=9.5)
        t.append(a)
        t.append(b)
        t.append(c)
        t.append(d)
        assert t[-4]['name'] == 'John'
        assert t[-3]['name'] == 'Mary'
        assert t[-2]['name'] == 'Fred'
        assert t[-1]['name'] == 'Wilma'
        assert t[-4].asDict() == {'name': 'John', 'age': 26, 'rating': 7.25}
        assert t[-3].asList() == b
        assert t[-2].asDict() == c
        assert t[-1].asList() == ['Wilma', 27, 9.5]

        # Printing
        # print t

        # Writing file (CSV)
        answer = '''\
name,age,rating
John,26,7.25
Mary,32,8.5
Fred,28,9.0
Wilma,27,9.5
'''
        out = StringIO()
        t.writeFile(out)
        results = out.getvalue()
        assert results == answer, '\n%r\n%r\n' % (results, answer)

        # Accessing rows
        for row in t:
            assert row['name'] == row[0]
            assert row['age'] == row[1]
            assert row['rating'] == row[2]
            for item in row:
                pass

        # Default type
        t = DataTable(defaultType='int')
        t.setHeadings(list('xyz'))
        t.append([1, 2, 3])
        t.append([4, 5, 6])
        assert t[0]['x'] - t[1]['z'] == -5

    def testBasics(self):
        # Basics
        src = '''\
"x","y,y",z
a,b,c
a,b,"c,d"
"a,b",c,d
"a","b","c"
"a",b,"c"
"a,b,c"
"","",""
"a","",
'''
        headings = ['x', 'y,y', 'z']
        data = [
            ['a', 'b', 'c'],
            ['a', 'b', 'c,d'],
            ['a,b', 'c', 'd'],
            ['a', 'b', 'c'],
            ['a', 'b', 'c'],
            ['a,b,c', '', ''],
            ['', '', ''],
            ['a', '', '']
        ]
        self._testSource('Basics', src, headings, data)

        # Comments
        src = '''\
a:int,b:int
1,2
#3,4
5,6
'''
        headings = ['a', 'b']
        data = [
            [1, 2],
            [5, 6],
        ]
        self._testSource('Comments', src, headings, data)

        # Multiline records
        src = '''\
a
"""Hi
there"""
'''
        headings = ['a']
        data = [
            ['"Hi\nthere"'],
        ]
        self._testSource('Multiline records', src, headings, data)

        # MiddleKit enums
        src = '''\
Class,Attribute,Type,Extras
#Foo,
,what,enum,"Enums=""foo, bar"""
,what,enum,"Enums='foo, bar'"
'''
        headings = 'Class,Attribute,Type,Extras'.split(',')
        data = [
            ['', 'what', 'enum', 'Enums="foo, bar"'],
            ['', 'what', 'enum', "Enums='foo, bar'"],
        ]
        self._testSource('MK enums', src, headings, data)

        # Unfinished multiline record
        try:
            DataTable().readString('a\n"1\n')
        except DataTableError:
            pass # just what we were expecting
        else:
            raise Exception(
                'Failed to raise exception for unfinished multiline record')

    def testExcelWithPickle(self):
        DataTable.usePickleCache = True
        self._testExcel()
        self._testExcel()

    def testExcelWithoutPickle(self):
        DataTable.usePickleCache = False
        self._testExcel()

    def _testExcel(self):
        if DataTable.canReadExcel():
            import sys
            sys.stderr = sys.stdout
            # print 'Testing Excel...'
            xlsfile = os.path.join(os.path.dirname(__file__), 'Sample3.xls')
            t = DataTable(xlsfile)
            assert t[0][0] == 1.0, t[0]


if __name__ == '__main__':
    unittest.main()

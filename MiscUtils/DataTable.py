'''
DataTable.py


INTRODUCTION

This class is useful for reading delimited text files which typically
have well defined columns or fields with several rows each of which can
be thought of as a record.

Using a DataTable can be as easy as using lists and dictionaries:

	table = DataTable('users.csv')
	for row in table:
		print row['name'], row['phoneNumber']

Or even:

	table = DataTable('users.csv')
	for row in table:
		print '%(name)s %(phoneNumber)s' % row

The above print statement relies on the fact that rows can be treated
like dictionaries, using the column headings as keys.

You can also treat a row like an array:

	table = DataTable('something.tabbed', delimiter='\t')
	for row in table:
		for item in row:
			print item,
		print


COLUMNS

Column headings can have a type specification like so:
	name, age:int, zip:int

Possible types include string, int, float and datetime. However,
datetime is not well supported right now.

String is assumed if no type is specified but you can set that
assumption when you create the table:

		table = DataTable(headings, defaultType='float')

Using types like int and float will cause DataTable to actually convert
the string values read from a file to these types so that you can use
them in natural operations. For example:

	if row['age']>120:
		self.flagData(row, 'age looks high')

As you can see, each row can be accessed as a dictionary with keys
according the column headings. Names are case sensitive.


ADDING ROWS

Like Python lists, data tables have an append() method. You can append
TableRecords, or you pass a dictionary, list of object, in which case a
TableRecord is created based on given values. See the method docs below
for more details.


FILES

By default, the files that DataTable reads from are expected to be
comma-separated value files.

Limited comments are supported: A comment is any line whose very first
character is a #. This allows you to easily comment out lines in your
data files without having to remove them.

Whitespace around field values is stripped.

You can control all this behavior through the arguments found in the
initializer and the various readSomething() methods:

	...delimiter=',', allowComments=1, stripWhite=1

For example:

	table = DataTable('foo.tabbed', delimiter='\t', allowComments=0, stripWhite=0)

You should access these parameters by their name since additional ones
could appear in the future, thereby changing the order.


NON-FILE TABLES

Here's an example that constructs a table from scratch:

	table = DataTable(['name', 'age:int'])
	table.append(['John', 80])
	table.append({'name': 'John', 'age': 80})
	print table


QUERIES

A simple query mechanism is supported for equality of fields:

	matches = table.recordsEqualTo({'uid': 5})


COMMON USES

* Servers can use data table to read and write log files.

* Programs can keep configuration and other data in simple comma-
separated text files and use DataTable to access them. For example, a
web site could read it's sidebar links from such a file, thereby
allowing people who don't know Python (or even HTML) to edit these
links without having to understand other implementation parts of the
site.


MORE DOCS

Some of the methods in this module have worthwhile doc strings to look
at.


TO DO

* Better support for datetime.
* Add error checking that a column name is not a number (which could
  cause problems).
* _types and BlankValues aren't really packaged, advertised or
  documented for customization by the user of this module.
* DataTable:
	* Parameterize the TextColumn class.
	* Parameterize the TableRecord class.
	* More list-like methods such as insert()
	* writeFileNamed() is flawed: it doesn't write the table column
	  type
	* Doesn't support quoted values and embedded commas
	* Should it inherit from UserList?
* Look for various @@ tags through out the code.

'''


import string
from string import join, split, strip
from types import *


## Types ##

DateTimeType = "<custom-type 'datetime'>"
ObjectType = "<type 'Object'>"

_types = {
	'string':	StringType,
	'int':		IntType,
	'float':	FloatType,
	'datetime':	DateTimeType,
	'object':	ObjectType,
}


## Classes ##


class DataTableError(Exception):
	pass


class TableColumn:
	'''
	A table column represents a column of the table including name and
	type.

	It does not contain the actual values of the column. These are
	stored individually in the rows.
	'''

	def __init__(self, spec):

		# spec is a string such as 'name' or 'name:type'
		fields = split(spec, ':')
		if len(fields)>2:
			raise DataTableError, 'Invalid column spec %s' % repr(spec)
		self._name = fields[0]

		if len(fields)==1:
			self._type = None
		else:
			self.setType(fields[1])

	def name(self):
		return self._name

	def type(self):
		return self._type

	def setType(self, type):
		''' Sets the type (by a string containing the name) of the heading. Usually invoked by DataTable to set the default type for columns whose types were not specified. '''
		if type==None:
			self._type = None
		else:
			try:
				self._type = _types[type]
			except:
				raise DataTableError, 'Unknown type %s' % repr(spec)

	def __repr__(self):
		return '<TableColumn %s with %s at %x>' % (
			repr(self._name), repr(self._type), id(self))

	def __str__(self):
		return self._name


	## Utilities ##

	def valueForRawValue(self, rawValue):
		''' The rawValue is typically a string or value already of the appropriate type. TableRecord invokes this method to ensure that values (especially strings that come from files) are the correct types (e.g., ints are ints and floats are floats). '''
		# @@ 2000-07-23 ce: an if-else ladder? perhaps these should be dispatched messages
		if self._type is StringType:
			value = str(rawValue)
		elif self._type is IntType:
			if rawValue=='':
				value = 0
			else:
				value = int(rawValue)
		elif self._type is FloatType:
			if rawValue=='':
				value = 0.0
			else:
				value = float(rawValue)
		elif self._type is DateTimeType:
			value = DateTime().initFromString(rawValue)
		elif self._type is ObjectType:
			value = rawValue
		else:
			raise DataTableError, 'Unknown column type "%s"' % self._type
		return value


class DataTable:
	'''
	'''

	## Init ##

	def __init__(self, filenameOrHeadings=None, delimiter=',', allowComments=1, stripWhite=1, defaultType='string'):
		if not _types.has_key(defaultType):
			raise DataTableError, 'Unknown type for default type: %s' % repr(defaultType)
		self._defaultType = defaultType
		self._filename = None
		self._headings = []
		self._rows = []
		if filenameOrHeadings:
			if type(filenameOrHeadings) is StringType:
				self.readFileNamed(filenameOrHeadings, delimiter, allowComments, stripWhite)
			else:
				self.setHeadings(filenameOrHeadings)


	## File I/O ##

	def readFileNamed(self, filename, delimiter=',', allowComments=1, stripWhite=1):
		self._filename = filename
		file = open(self._filename, 'r')
		self.readFile(file, delimiter, allowComments, stripWhite)
		file.close()
		return self

	def readFile(self, file, delimiter=',', allowComments=1, stripWhite=1):
		return self.readLines(file.readlines(), delimiter, allowComments, stripWhite)

	def readString(self, string, delimiter=',', allowComments=1, stripWhite=1):
		return self.readLines(split(string, '\n'), delimiter, allowComments, stripWhite)

	def readLines(self, lines, delimiter=',', allowComments=1, stripWhite=1):
		if not lines:
			return self
		readHeadings = 0
		lineNumber = 0
		lenLines = len(lines)
		while lineNumber<lenLines:
			line = lines[lineNumber]

			# skip comments
			if not line:
				# skip blanks
				pass
			elif line[0]=='#':
				# skip comments
				pass
			elif readHeadings:
				# process data rows

				# Split into a list of values
				values = split(line, delimiter)
				if stripWhite:
					values = map(strip, values)

				# Create a record using the headings and the current values
				row = TableRecord(self, values)
				self._rows.append(row)
			else:
				# process headings
				headings = split(line, delimiter)
				if headings==None  or  len(headings)==0:
					raise DataTableError, "Couldn't read valid headings"
				if stripWhite:
					headings = map(strip, headings)
				self.setHeadings(headings)
				self.createNameToIndexMap()
				readHeadings = 1

			lineNumber = lineNumber + 1

		return self

	def save(self):
		self.writeFileNamed(self._filename)

	def writeFileNamed(self, filename):
		file = open(filename, 'w')
		self.writeFile(file)
		file.close()

	def writeFile(self, file):
		'''
		@@ 2000-07-20 ce: This doesn't write the column types (like :int) back out.
		@@ 2000-07-21 ce: It's notable that a blank numeric value gets read as zero and written out that way. Also, values None are written as blanks.
		'''

		# write headings
		file.write(join(map(lambda h: str(h), self._headings), ','))
		file.write('\n')

		def ValueWritingMapper(item):
			# So that None gets written as a blank and everything else as a string
			if item is None:
				return ''
			else:
				return str(item)

		# write rows
		for row in self._rows:
			file.write(join(map(ValueWritingMapper, row), ','))
			file.write('\n')

	def commit(self):
		if self._changed:
			self.save()
			self._changed = 0


	## Headings ##

	def heading(self, index):
		if type(key) is StringType:
			key = self._nameToIndexMap[key]
		return self._headings[index]

	def hasHeading(self, name):
		return self._nameToIndexMap.has_key(name)

	def numHeadings(self):
		return len(self._headings)

	def headings(self):
		return self._headings

	def setHeadings(self, headings):
		''' Headings can be a list of strings (like ['name', 'age:int']) or a list of TableColumns or None. '''
		if not headings:
			self._headings = []
		elif type(headings[0]) is StringType:
			self._headings = map(lambda h: TableColumn(h), headings)
		elif isinstance(headings[0], TableColumn):
			self._headings = list(headings)
		for heading in self._headings:
			if heading.type() is None:
				heading.setType(self._defaultType)
		self.createNameToIndexMap()


	## Row access (list like) ##

	def __len__(self):
		return len(self._rows)

	def __getitem__(self, index):
		return self._rows[index]

	def append(self, object):
		''' If object is not a TableRecord, then one is created, passing the object to initialize the TableRecord. Therefore, object can be a TableRecord, list, dictionary or object. See TableRecord for details. '''

		if not isinstance(object, TableRecord):
			object = TableRecord(self, object)
		self._rows.append(object)
		self._changed = 1


	## Queries ##

	def recordsEqualTo(self, dict):
		records = []
		keys = dict.keys()
		for record in self._rows:
			matches = 1
			for key in keys:
				if record[key]!=dict[key]:
					matches = 0
					break
			if matches:
				records.append(record)
		return records


	## As a string ##

	def __repr__(self):
		# Initial info
		s = ['DataTable: %s\n%d rows\n' % (self._filename, len(self._rows))]

		# Headings
		s.append('     ')
		s.append(join(map(lambda h: str(h), self._headings), ', '))
		s.append('\n')

		# Records
		i = 0
		for row in self._rows:
			s.append('%3d. ' % i)
			s.append(join(map(lambda r: str(r), row), ', '))
			s.append('\n')
			i = i + 1
		return join(s, '')


	## Misc access ##

	def filename(self):
		return self._filename

	def nameToIndexMap(self):
		''' Table rows keep a reference to this map in order to speed up index-by-names (as in row['name']). '''
		return self._nameToIndexMap


	## Self utilities ##

	def createNameToIndexMap(self):
		''' Invoked by self to create the nameToIndexMap after the table's headings have been read/initialized. '''
		map = {}
		for i in range(len(self._headings)):
			map[self._headings[i].name()] = i
		self._nameToIndexMap = map


# @@ 2000-07-20 ce: perhaps for each type we could specify a function to convert from string values to the values of the type

BlankValues = {
	StringType:   '',
	IntType:      '0',
	FloatType:    '0.0',
	DateTimeType: '',
}


class TableRecord:

	def __init__(self, table, values=None):
		'''
		Dispatches control to one of the other init method based on the type of values.  Values can be one of three things:
			1. A TableRecord
			2. A list
			3. A dictionary
			4. Any object responding to hasValueForField() and valueForField().
		'''
 		self._headings = table.headings()
		self._nameToIndexMap = table.nameToIndexMap()
		# @@ 2000-07-20 ce: Take out the headings arg to the init method since we have an attribute for that

		if values is not None:
			valuesType = type(values)
			if valuesType is ListType  or  valuesType is TupleType:
				# @@ 2000-07-20 ce: check for required attributes instead
				self.initFromSequence(values)
			elif valuesType is DictType:
				self.initFromDict(values)
			elif valuesType is InstanceType:
				self.initFromObject(value)
			else:
				raise DataTableError, 'Unknown type for values %s.' % valuesType

	def initFromSequence(self, values):
		if len(self._headings)<len(values):
			raise DataTableError, ('There are more values than headings.\nheadings(%d, %s)\nvalues(%d, %s)' % (len(self._headings), self._headings, len(values), values))
		self._values = []
		numHeadings = len(self._headings)
		numValues = len(values)
		assert numValues<=numHeadings
		for i in range(numHeadings):
			heading = self._headings[i]
			if i>=numValues:
				self._values.append(BlankValues[heading.type()])
			else:
				self._values.append(heading.valueForRawValue(values[i]))

	def initFromDict(self, dict):
		self._values = []
		for heading in self._headings:
			name = heading.name()
			if dict.has_key(name):
				self._values.append(heading.valueForRawValue(dict[name]))
			else:
				self._values.append(BlankValues[heading.type()])

	def initFromObject(self, object):
		''' The object is expected to response to hasValueForField(name) and valueForField(name) for each of the headings in the table. It's alright if the object returns 0 for hasValueForField(). In that case, a "blank" value is assumed (such as zero or an empty string). If hasValueForField() returns 1, then valueForField() must return a value. '''
		self._values = []
		for heading in self._headings:
			name = heading.name()
			if object.hasValueForField(name):
				self._values.append(heading.valueForRawValue(object.valueForField(name)))
			else:
				self._values.append(BlankValues[heading.type()])


	## Access ##

	def __len__(self):
		return len(self._values)

	def __getitem__(self, key):
		if type(key) is StringType:
			key = self._nameToIndexMap[key]
		return self._values[key]

	def __setitem__(self, key, value):
		if type(key) is StringType:
			key = self._nameToIndexMap[key]
		self._values[key] = value

	def __repr__(self):
		return '%s' % self._values

from CodeGenerator import *
import os, sys
from glob import glob
from time import asctime, localtime, time
from MiddleKit import StringTypes
from MiddleKit.Core.ObjRefAttr import objRefJoin
from MiscUtils import CSVParser
import string

class SampleError:
	def __init__(self,line,error):
		self._line = line
		self._error = error

	def output(self,filename):
		print '%s:%d: %s' % ( filename, self._line, self._error )


class SQLGenerator(CodeGenerator):
	"""
	This class and its associated mix-ins are responsible for generating:
		- Create.sql
		- InsertSample.sql
		- Info.text

	A subclass and further mix-ins are required for specific databases (since SQL varies from product to product).

	The main method to invoke is generate():

		gen = SomeSQLGenerator()
		gen.readModelFileNamed(filename)
		gen.generate(dirname)

	For subclassers:
		- Subclasses should be named <DATABASE>SQLGenerator where <DATABASE> is the name of the particular database product.
		- A good example of a custom subclass is MySQLSQLGenerator.py. Be sure to take a look at it.
		- Candidates for customization include:
			Klasses
				dropDatabaseSQL()
				createDatabaseSQL()
				useDatabaseSQL()
			StringAttr
			EnumAttr
	"""

	def sqlDatabaseName(self):
		"""
		Returns the name of the database by asking the generator's
		model.
		"""
		return self.model().sqlDatabaseName()

	def generate(self, dirname):
		self.requireDir(dirname)
		self.writeInfoFile(os.path.join(dirname, 'Info.text'))
		self._model.writeCreateSQL(self, dirname)
		self._model.writeInsertSamplesSQL(self, dirname)

	def sqlSupportsDefaultValues(self):
		"""
		Subclasses must override to return 1 or 0, indicating their SQL variant supports DEFAULT <value> in the CREATE statement.
		Subclass responsibility.
		"""
		raise SubclassResponsibility


class ModelObject:
	pass


class Model:

	def writeCreateSQL(self, generator, dirname):
		"""
		Creates the directory if necessary, sets the klasses' generator, and tells klasses to writeCreateSQL().
		"""
		if not os.path.exists(dirname):
			os.mkdir(dirname)
		assert os.path.isdir(dirname)
		self._klasses.setSQLGenerator(generator)
		self._klasses.writeCreateSQL(generator, os.path.join(dirname, 'Create.sql'))

	def sqlDatabaseName(self):
		"""
		Returns the name of the database (which is either the 'Database'
		setting or self.name()).
		"""
		name = self.setting('Database', None)
		if name is None:
			name = self.name()
		return name

	def writeInsertSamplesSQL(self, generator, dirname):
		if self._filename is not None:
			file = open(os.path.join(dirname, 'InsertSamples.sql'), 'w')
			file.write('use %s;\n\n' % self.sqlDatabaseName())
			self._klasses.writeDeleteAllRecords(generator, file)
			filenames = glob(os.path.join(self._filename, 'Sample*.csv'))
			for filename in filenames:
				lines = open(filename).readlines()
				try:
					self.writeInsertSamplesSQLForLines(lines, generator, file, filename)
				except SampleError, s:
					s.output( filename )
					sys.exit(1)
			file.close()

	def writeInsertSamplesSQLForLines(self, lines, generator, file, filename):
		# @@ 2001-02-04 ce: this method is too long
		#	break into additional methods
		#	some of these methods may even go into other mix-ins
		readColumns = 1
		parse = CSVParser.CSVParser().parse
		linenum = 0
		for line in lines:
			linenum += 1
			try:
				fields = parse(line)
			except CSVParser.ParseError, err:
				raise SampleError(linenum, 'Syntax error: %s' % err)
			if fields is None:	# parser got embedded newline; continue with the next line
				continue

			try:
				if self.areFieldsBlank(fields):
					continue  # skip blank lines
				if fields[0] and str(fields[0])[0]=='#':
					continue
				if fields[0].endswith(' objects'):
					tableName = fields[0].split()[0]
					try:
						klass = self.klass(tableName)
					except KeyError:
						raise SampleError( linenum, "Class '%s' has not been defined" % ( tableName ) )
					file.write('\n\n/* %s */\n\n' % fields[0])
					#print '>> table:', tableName
					readColumns = 1
					continue
				if readColumns:
					names = [name for name in fields if name]
					attrs = []
					for name in names:
						if name==klass.sqlSerialColumnName():
							attrs.append(PrimaryKey(name, klass))
						else:
							try:
								attrs.append(klass.lookupAttr(name))
							except KeyError:
								raise SampleError( linenum, "Class '%s' has no attribute '%s'" % ( klass.name(), name ) )
					# @@ 2000-10-29 ce: check that each attr.hasSQLColumn()
					for attr in attrs:
						assert not attr.get('isDerived', 0)
					colNames = [attr.sqlName() for attr in attrs]
					#print '>> cols:', columns
					colSql = ','.join(colNames)
					readColumns = 0
					continue
				values = fields[:len(attrs)]
				i = 0
				for attr in attrs:
					try:
						value = values[i]
					except IndexError:
						raise SampleError( linenum, "Couldn't find value for attribute '%s'" % attr.name() )
					values[i] = attr.sqlForSampleInput(value)
					assert len(values[i])>0, repr(values[i])  # SQL value cannot be blank
					i += 1
				#print
				#values = [self.valueFilter(value) for value in values]
				values = ', '.join(values)
				stmt = 'insert into %s (%s) values (%s);\n' % (tableName, colSql, values)
				file.write(stmt)
			except:
				print
				print 'Samples error:'
				try:
					print '%s:%s' % (filename, linenum)
					print line
				except:
					pass
				print
				raise

	def areFieldsBlank(self, fields):
		""" Utility method for writeInsertSamplesSQLForLines(). """
		if len(fields)==0:
			return 1
		for field in fields:
			if field:
				return 0
		return 1


class Klasses:

	def sqlGenerator(self):
		return generator

	def setSQLGenerator(self, generator):
		self._sqlGenerator = generator

	def auxiliaryTableNames(self):
		""" Returns a list of table names in addition to the tables that hold objects. One popular user of this method is dropTablesSQL(). """
		return ['_MKClassIds']

	def writeKeyValue(self, out, key, value):
		""" Used by willCreateWriteSQL(). """
		key = key.ljust(12)
		out.write('# %s = %s\n' % (key, value))

	def writeCreateSQL(self, generator, out):
		""" Writes the SQL to define the tables for a set of classes. The target can be a file or a filename. """
		if isinstance(out, StringTypes):
			out = open(out, 'w')
			close = 1
		else:
			close = 0
		self.willWriteCreateSQL(generator, out)
		self._writeCreateSQL(generator, out)
		self.didWriteCreateSQL(generator, out)
		if close:
			out.close()

	def willWriteCreateSQL(self, generator, out):
		# @@ 2001-02-04 ce: break up this method
		wr = out.write
		kv = self.writeKeyValue
		wr('/*\nStart of generated SQL.\n\n')
		kv(out, 'Date', asctime(localtime(time())))
		kv(out, 'Python ver', sys.version)
		kv(out, 'Op Sys', os.name)
		kv(out, 'Platform', sys.platform)
		kv(out, 'Cur dir', os.getcwd())
		kv(out, 'Num classes', len(self._klasses))
		wr('\nClasses:\n')
		for klass in self._model._allKlassesInOrder:
			wr('\t%s\n' % klass.name())
		wr('*/\n\n')

		sql = generator.setting('PreSQL', None)
		if sql:
			wr('/* PreSQL start */\n' + sql + '\n/* PreSQL end */\n\n')

		dbName = generator.sqlDatabaseName()
		drop = generator.setting('DropStatements')
		if drop=='database':
			wr(self.dropDatabaseSQL(dbName))
			wr(self.createDatabaseSQL(dbName))
			wr(self.useDatabaseSQL(dbName))
		elif drop=='tables':
			wr(self.useDatabaseSQL(dbName))
			wr(self.dropTablesSQL())
		else:
			raise Exception, 'Invalid value for DropStatements setting: %r' % drop

	def dropDatabaseSQL(self, dbName):
		"""
		Returns SQL code that will remove the database with the given name.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def dropTablesSQL(self):
		"""
		Returns SQL code that will remove each of the tables in the database.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def createDatabaseSQL(self, dbName):
		"""
		Returns SQL code that will create the database with the given name.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def useDatabaseSQL(self, dbName):
		"""
		Returns SQL code that will use the database with the given name.
		Used by willWriteCreateSQL().
		Subclass responsibility.
		"""
		raise AbstractError, self.__class__

	def _writeCreateSQL(self, generator, out):
		# assign the class ids up-front, so that we can resolve forward object references
		self.assignClassIds(generator)
		self.writeClassIdsSQL(generator, out)
		for klass in self._model._allKlassesInOrder:
			klass.writeCreateSQL(self._sqlGenerator, out)

	def writeClassIdsSQL(self, generator, out):
		wr = out.write
		wr('''\
create table _MKClassIds (
	id int not null primary key,
	name varchar(100)
);
''')
		values = []
		for klass in self._model._allKlassesInOrder:
			wr('insert into _MKClassIds (id, name) values ')
			wr("\t(%s, '%s');\n" % (klass.id(), klass.name()))
		wr('\n')


	def listTablesSQL(self):
		# return a SQL command to list all tables in the database
		# this is database-specific, so by default we return nothing
		return ''

	def didWriteCreateSQL(self, generator, out):
		sql = generator.setting('PostSQL', None)
		if sql:
			out.write('/* PostSQL start */\n' + sql + '\n/* PostSQL end */\n\n')
		out.write(self.listTablesSQL())
		out.write('/* end of generated SQL */\n')

	def writeDeleteAllRecords(self, generator, file):
		"""
		Writes a delete statement for each data table in the model. This is used for InsertSamples.sql to wipe out all data prior to inserting sample values.
		SQL generators rarely have to customize this method.
		"""
		wr = file.write
		if 0:
			# Woops. Our only auxiliary table is _MKClassIds, which we
			# *don't* want to delete. In the future we will likely
			# have other aux tables for lists and relationships. When
			# that happens, we'll need more granularity regarding
			# aux tables.
			names = self.auxiliaryTableNames()[:]
			names.reverse()
			for tableName in names:
				wr('delete from %s;\n' % tableName)
		klasses = self._model._allKlassesInOrder[:]
		klasses.reverse()
		for klass in klasses:
			if not klass.isAbstract():
				wr('delete from %s;\n' % klass.sqlTableName()) # dr 7-12-02: changed from klass.name()
		wr('\n')



import KlassSQLSerialColumnName


class Klass:

	def writeCreateSQL(self, generator, out):
		for attr in self.attrs():
			attr.writeAuxiliaryCreateTable(generator, out)
		if not self.isAbstract():
			self.writeCreateTable(generator, out)

	def writeCreateTable(self, generator, out):
		name = self.name()
		wr = out.write
		wr('create table %s (\n' % self.sqlTableName())
		wr(self.primaryKeySQLDef(generator))
		if generator.model().setting('DeleteBehavior', 'delete') == 'mark':
			wr(self.deletedSQLDef(generator))
		first = 1
		sqlAttrs = []
		nonSQLAttrs = []
		for attr in self.allAttrs():
			if attr.hasSQLColumn():
				sqlAttrs.append(attr)
			else:
				nonSQLAttrs.append(attr)
		for attr in sqlAttrs:
			if first:
				first = 0
			else:
				wr(',\n')
			attr.writeCreateSQL(generator, out)
		self.writeIndexSQLDefs(wr)
		for attr in nonSQLAttrs:
			attr.writeCreateSQL(generator, out)
			wr('\n')
		wr(');\n\n\n')

	def primaryKeySQLDef(self, generator):
		"""
		Returns a one liner that becomes part of the CREATE statement
		for creating the primary key of the table. SQL generators often
		override this mix-in method to customize the creation of the
		primary key for their SQL variant. This method should use
		self.sqlSerialColumnName() and often ljust()s it by
		self.maxNameWidth().
		"""
		return '    %s int not null primary key,\n' % self.sqlSerialColumnName().ljust(self.maxNameWidth())

	def deletedSQLDef(self, generator):
		"""
		Returns a one liner that becomes part of the CREATE statement
		for creating the deleted timestamp field of the table.
		This is used if DeleteBehavior is set to "mark".
		"""
		return '    %s datetime null,\n' % ('deleted'.ljust(self.maxNameWidth()))

	def maxNameWidth(self):
		return 30   # @@ 2000-09-15 ce: Ack! Duplicated from Attr class below

	def writeIndexSQLDefs(self, wr):
		for attr in self.allAttrs():
			if attr.get('isIndexed', 0) and attr.hasSQLColumn():
				wr(',\n')
				wr('\tindex (%s)' % attr.sqlName())
		wr('\n')

	def sqlTableName(self):
		"""
		Can be overidden to allow for table names that do not conflict with SQL
		reserved words. dr 08-08-2002 - MSSQL uses [tablename]
		"""
		return '%s' % self.name()


class Attr:

	def sqlName(self):
		return self.name()

	def hasSQLColumn(self):
		""" Returns true if the attribute has a direct correlating SQL column in it's class' SQL table definition. Most attributes do. Those of type list do not. """
		return not self.get('isDerived', 0)

	def sqlForSampleInput(self, input):
		input = input.strip()
		if input=='':
			input = self.get('Default', '')
		if input in (None, 'None', 'none'):
			return self.sqlForNone()
		else:
			return str(self.sqlForNonNoneSampleInput(input))

	def sqlForNone(self):
		return 'NULL'

	def sqlForNonNoneSampleInput(self, input):
		return input

	def writeCreateSQL(self, generator, out):
		try:
			if self.hasSQLColumn():
				self.writeRealCreateSQLColumn(generator, out)
			else:
				out.write('\t/* %(Name)s %(Type)s - not a SQL column */' % self)
		except:
			bar = '*'*78
			print
			print bar
			print 'exception for attribute:'
			print '%s.%s' % (self.klass().name(), self.name())
			print
			try:
				from pprint import pprint
				pprint(self.data)
			except:
				pass
			print bar
			print
			raise

	def writeRealCreateSQLColumn(self, generator, out):
		name = self.sqlName().ljust(self.maxNameWidth())
		if self.isRequired():
			notNullSQL = ' not null'
		else:
			notNullSQL = self.sqlNullSpec()
		if generator.sqlSupportsDefaultValues():
			defaultSQL = self.createDefaultSQL()
			if defaultSQL:
				defaultSQL = ' ' + defaultSQL
		else:
			defaultSQL = ''
		out.write('\t%s %s%s%s' % (name, self.sqlType(), notNullSQL, defaultSQL))

	def writeAuxiliaryCreateTable(self, generator, out):
		# most attribute types have no such beast
		pass

	def sqlNullSpec(self):
		return ''

	def createDefaultSQL(self):
		default = self.get('SQLDefault', None)
		if default is None:
			default = self.get('Default', None)
			if default is not None:
				default = self.sqlForSampleInput(str(default))
		if default:
			default = str(default).strip()
			if default.lower()=='none':  # kind of redundant
				default = None
			return 'default ' + default
		else:
			return ''

	def maxNameWidth(self):
		return 30  # @@ 2000-09-14 ce: should compute that from names rather than hard code

	def sqlType(self):
		raise AbstractError, self.__class__

	def sqlColumnName(self):
		"""
		Returns the SQL column name corresponding to this attribute
		which simply defaults to the attribute's name. Subclasses may
		override to customize.
		"""
		if not self._sqlColumnName:
			self._sqlColumnName = self.name()
		return self._sqlColumnName


class BoolAttr:

	def sqlType(self):
		# @@ 2001-02-04 ce: is this ANSI SQL? or at least common SQL?
		return 'bool'

	def sqlForNonNoneSampleInput(self, input):
		try:
			value = input.upper()
		except:
			pass
		if value in ('FALSE', 'NO', '0', '0.0', 0, 0.0):
			value = 0
		elif value in ('TRUE', 'YES', '1', '1.0', 1, 1.0):
			value = 1
		assert value==0 or value==1, value
		return str(value)


class IntAttr:

	def sqlType(self):
		return 'int'

	def sqlForNonNoneSampleInput(self, input):
		if not isinstance(input, int):
			value = str(input)
			if value.endswith('.0'):
				# numeric values from Excel-based models are always float
				value = value[:-2]
			int(value) # raises exception if value is invalid
			return value


class LongAttr:

	def sqlType(self):
		# @@ 2000-10-18 ce: is this ANSI SQL?
		return 'bigint'

	def sqlForNonNoneSampleInput(self, input):
		long(input) # raises exception if value is invalid
		return input


class FloatAttr:

	def sqlType(self):
		return 'double precision'

	def sqlForNonNoneSampleInput(self, input):
		float(input) # raises exception if value is invalid
		return input


class DecimalAttr:

	def sqlType(self):
		# the keys 'Precision' and 'Scale' are used because all the
		# SQL docs I read say:  decimal(precision, scale)
		precision = self.get('Precision', None)
		if precision is None:
			if self.klass().klasses()._model.setting('UseMaxForDecimalPrecision', 0):  # that setting is for backwards compatibility
				precision = self.get('Max', None)
				if not precision:
					precision = None
			if precision is None:
				precision = 11
		scale = self.get('Scale', None)
		if scale is None:
			scale = self.get('numDecimalPlaces', 3)
		return 'decimal(%s,%s)' % (precision, scale)

	def sqlForNonNoneSampleInput(self, input):
		return input


class StringAttr:

	def sqlType(self):
		"""
		Subclass responsibility.
		Subclasses should take care that if self['Max']==self['Min'] then the "char" type is preferred over "varchar".
		Also, most (if not all) SQL databases require different types depending on the length of the string.
		"""
		raise AbstractError, self.__class__

	def sqlForNonNoneSampleInput(self, input):
		value = input
		if value=="''":
			value = ''
		elif value.find('\\')!=-1:
			if 1:
				# add spaces before and after, to prevent
				# syntax error if value begins or ends with "
				value = eval('""" '+str(value)+' """')
				value = repr(value[1:-1])	# trim off the spaces
				value = value.replace('\\011', '\\t')
				value = value.replace('\\012', '\\n')
				return value
		value = repr(value)
		#print '>> value:', value
		return value


class AnyDateTimeAttr:

	def sqlType(self):
		return self['Type']  # e.g., date, time and datetime

	def sqlForNonNoneSampleInput(self, input):
		return repr(input)


class ObjRefAttr:

	def sqlName(self):
		if self.setting('UseBigIntObjRefColumns', False):
			return self.name() + 'Id'  # old way: one 64 bit column
		else:
			# new way: 2 int columns for class id and obj id
			name = self.name()
			classIdName, objIdName = self.setting('ObjRefSuffixes')
			classIdName = name + classIdName
			objIdName = name + objIdName
			return '%s,%s' % (classIdName, objIdName)

	def writeRealCreateSQLColumn(self, generator, out):
		if self.setting('UseBigIntObjRefColumns', False):
			# the old technique of having both the class id and the obj id in one 64 bit reference
			name = self.sqlName().ljust(self.maxNameWidth())
			if self.get('Ref', None):
				refs = ' references %(Type)s(%(Type)sId)' % self
			else:
				refs = ''
			if self.isRequired():
				notNull = ' not null'
			else:
				notNull = self.sqlNullSpec()
			out.write('\t%s %s%s%s' % (name, self.sqlType(), refs, notNull))
		else:
			# the new technique uses one column for each part of the obj ref: class id and obj id
			classIdName = self.name()+self.setting('ObjRefSuffixes')[0]
			classIdName = classIdName.ljust(self.maxNameWidth())
			objIdName = self.name()+self.setting('ObjRefSuffixes')[1]
			objIdName = objIdName.ljust(self.maxNameWidth())
			if self.isRequired():
				notNull = ' not null'
			else:
				notNull = self.sqlNullSpec()
			classIdDefault = ' default %s' % self.targetKlass().id()
			#   ^ this makes the table a little to easier to work with in some cases (you can often just insert the obj id)
			if self.get('Ref', None):
				objIdRef = ' references %(Type)s(%(Type)sId) ' % self
			else:
				objIdRef = ''
			out.write('\t%s %s%s%s references _MKClassIds, /* %s */ \n' % (classIdName, self.sqlType(), notNull, classIdDefault, self.targetClassName()))
			out.write('\t%s %s%s%s' % (objIdName, self.sqlType(), notNull, objIdRef))

	def sqlForNone(self):
		if self.setting('UseBigIntObjRefColumns', False):
			return 'NULL'
		else:
			return 'NULL,NULL'

	def sqlForNonNoneSampleInput(self, input):
		"""
		Obj ref sample data format is "Class.serialNum", such as
		"Thing.3". If the Class and period are missing, then the obj
		ref's type is assumed.
		"""
		parts = input.split('.')
		if len(parts)==2:
			className = parts[0]
			objSerialNum = parts[1]
		else:
			className = self.targetClassName()
			objSerialNum = input
		klass = self.klass().klasses()._model.klass(className)
		klassId = klass.id()
		if self.setting('UseBigIntObjRefColumns', False):
			objRef = objRefJoin(klassId, objSerialNum)
			return str(objRef)
		else:
			return '%s,%s' % (klassId, objSerialNum)


class ListAttr:

	def sqlType(self):
		raise Exception, 'Lists do not have a SQL type.'

	def hasSQLColumn(self):
		return 0

	def sqlForSampleInput(self, input):
		raise Exception, 'Lists are implicit. They cannot have sample values.'


class EnumAttr:

	def sqlType(self):
		if self.usesExternalSQLEnums():
			tableName, valueColName, nameColName = self.externalEnumsSQLNames()
			return 'int references %s(%s)' % (tableName, valueColName)
		else:
			return self.nativeEnumSQLType()

	def nativeEnumSQLType(self):
		maxLen = max([len(e) for e in self.enums()])
		return 'varchar(%s)' % maxLen

	def sqlForNonNoneSampleInput(self, input):
		if self.usesExternalSQLEnums():
			return self.intValueForString(input)
		else:
			assert input in self._enums, 'input=%r, enums=%r' % (input, self._enums)
			return repr(input)

	def writeAuxiliaryCreateTable(self, generator, out):
		if self.usesExternalSQLEnums():
			tableName, valueColName, nameColName = self.externalEnumsSQLNames()
			out.write('create table %s (\n' % tableName)
			out.write('\t%s int not null primary key,\n' % valueColName)
			out.write('\t%s varchar(255)\n' % nameColName)
			out.write(');\n')

			i = 0
			sep = ''
			for enum in self.enums():
				out.write("insert into %(tableName)s values (%(i)i, '%(enum)s');\n" % locals())
				i += 1
			out.write('\n')


	## Settings ##

	def usesExternalSQLEnums(self):
		flag = getattr(self, '_usesExternalSQLEnums', None)
		if flag is None:
			flag = self.model().usesExternalSQLEnums()
			self._usesExternalSQLEnums = flag
		return flag

	def externalEnumsSQLNames(self):
		"""
		Returns the tuple (tableName, valueColName, nameColName)
		derived from the model setting ExternalEnumsSQLNames.
		"""
		names = getattr(self, '_externalEnumsSQLNames', None)
		if names is None:
			_ClassName = self.klass().name()
			ClassName  = _ClassName[0].upper() + _ClassName[1:]
			className  = _ClassName[0].lower() + _ClassName[1:]
			_AttrName  = self.name()
			AttrName   = _AttrName[0].upper()  + _AttrName[1:]
			attrName   = _AttrName[0].lower()  + _AttrName[1:]
			values = locals()
			names = self.setting('ExternalEnumsSQLNames')
			names = [names['TableName'], names['ValueColName'], names['NameColName']]
			for i in range(len(names)):
				names[i] %= values
			self._externalEnumsSQLNames = names
		return names


class PrimaryKey:
	"""
	This class is not a 'standard' attribute, but just a helper class for the
	writeInsertSamplesSQLForLines method, in case the samples.csv file contains
	a primary key column (i.e. the serial numbers are specified explicitly).
	"""

	def __init__(self, name, klass):
		self._name = name
		self._klassid = klass.id()
		self._props = {'isDerived': 0}

	def name(self):
		return self._name

	def sqlName(self):
		return self.name()

	def get(self,key,default=0):
		return self._props.get(key,default)

	def sqlForNonNoneSampleInput(self, input):
		return input

from SQLGenerator import SQLGenerator
from SQLGenerator import PrimaryKey as PrimaryKeyBase
from MiscUtils.MixIn import MixIn
import psycopg as dbi  # psycopg adapter; apt-get install python2.2-psycopg

class PostgreSQLSQLGenerator(SQLGenerator):

	def sqlSupportsDefaultValues(self):
		return 1

class Model:
	def writePostSamplesSQL(self, generator, output):
		# after inserting the samples, update the sequences with the highest
		# serial numbers we've seen for each class.
		for klass in self._allKlassesInOrder:
			if hasattr(klass, '_maxSerialNum') and klass._maxSerialNum > 0:
				output.write("select setval('%s', %d);" % ( klass.seqName(), klass._maxSerialNum))
	
class Klasses:

	def dropDatabaseSQL(self, dbName):
		# errors are ignored
		return 'DROP DATABASE "%s";\n' % dbName

	def dropTablesSQL(self):
		sql = []
		names = self.auxiliaryTableNames()[:]
		names.reverse()
		for tableName in names:
			sql.append('drop table "%s";\n' % tableName)
		klasses = self._model._allKlassesInOrder[:]
		klasses.reverse()
		for klass in klasses:
			sql.append('drop table "%s";\n' % klass.name())
		sql.append('\n')
		return ''.join(sql)

	def createDatabaseSQL(self, dbName):
		return 'create database "%s";\n' % dbName

	def useDatabaseSQL(self, dbName):
		return '\c "%s"\n\n' % dbName

	def listTablesSQL(self):
		return '\d\n\n'


class Klass:

	def writeCreateSQL(self, generator, out):
		# create the sequences explicitly, just to be sure
		wr = out.write
		if not self.isAbstract():
			wr('create sequence %s start 1 minvalue 1;\n\n' % self.seqName())
		Klass.mixInSuperWriteCreateSQL(self, generator, out)
		self.writePgSQLIndexDefs(wr)

	def seqName(self):
		return '%s_%s_seq' % (self.sqlTableName(), self.sqlSerialColumnName())

	def writeIndexSQLDefs(self, wr):
		# in postgres, indices must be created with 'create index' commands
		pass

	def writePgSQLIndexDefs(self, wr):
		for attr in self.allAttrs():
			if attr.get('isIndexed', 0) and attr.hasSQLColumn():
				wr('create index %s_%s_index on %s (%s);\n' % (self.sqlTableName(), attr.sqlName(), self.sqlTableName(), attr.sqlName()))
		wr('\n')


	def primaryKeySQLDef(self, generator):
		return "\t%s integer not null primary key default nextval('%s'),\n" % (self.sqlSerialColumnName(), self.seqName())


## Enums are not supported directly by postgres, but we can emulate them
## using simple char columns.

class EnumAttr:

	def sqlType(self):
		lengths = map( lambda value: len(value), self.enums())
		return 'varchar(%d)' % max(lengths)

	def sampleValue(self, value):
		assert value in self._enums, 'value = %r, enums = %r' % (value, self._enums)
		return repr(value)


class StringAttr:

	def sqlType(self):
		# @@ 2000-11-11 ce: cache this
		if not self.get('Max', None):
			return 'varchar(100) /* WARNING: NO LENGTH SPECIFIED */'
		max = int(self['Max']) # @@ 2000-11-12 ce: won't need int() after using types
		if max>65535:
			return 'longtext'
		if max>255:
			return 'text'
		if self.has_key('Min') and self['Min'] and int(self['Min'])==max:
			return 'char(%s)' % max
		else:
			return 'varchar(%s)' % max

	def sampleValue(self, value):
		if value is None:
			value = 'NULL'
		else:
			value = "%s" % dbi.QuotedString(value)
		return value

class BoolAttr:

	def sampleValue(self, value):
		value = value.upper()
		if value=='FALSE' or value=='NO':
			value = 'TRUE'
		elif value=='TRUE' or value=='YES':
			value = 'FALSE'
		else:
			try:
				value = int(value)
				if value == 0:
					value = 'FALSE'
				elif value ==1:
					value = 'TRUE'
			except:
				pass
		assert value in ['TRUE','FALSE'], "'%s' is not a valid default for boolean column '%s'" % (value, self.name())
		return value


class ObjRefAttr:

	def sqlType(self):
		# @@ 2001-02-04 ce: Is this standard SQL? If so, it can be moved up.
		return 'bigint /* %s */' % self['Type']

class PrimaryKey:
	def sampleValue(self,value):
		# keep track of the highest serial number for each klass,
		# so that we can update the database sequences
		if int(value) > self._klass._maxSerialNum:
			self._klass._maxSerialNum = int(value)
		return value

# PrimaryKey is not a core class, so we have to mix this in manually.
MixIn(PrimaryKeyBase, PrimaryKey)

from SQLGenerator import SQLGenerator
from string import find, join, ljust, lower, split, strip, upper
from time import asctime, localtime, time
import os, sys


class MSSQLSQLGenerator(SQLGenerator):
	pass


# @@ 2000-09-14 ce: Some of the methods here are generic enough for SQLGenerator,
# but our class fusing code doesn't handle classes found in the modules of
# ancestor classes of the generator class.


class Model:

	def writeSQL(self, generator, dirname):
		if not os.path.exists(dirname):
			os.mkdir(dirname)
		assert os.path.isdir(dirname)
		self._klasses.setSQLGenerator(generator)
		self._klasses.writeSQL(generator, os.path.join(dirname, 'Create.sql'))


class Klasses:

	def sqlGenerator(self):
		return generator

	def setSQLGenerator(self, generator):
		self._sqlGenerator = generator

	def writeClassIdsSQL(self, generator, out):
		wr = out.write
# If _MKClassIds table exists drop it before creating it again.	
		wr('''\

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[_MKClassIds]') and OBJECTPROPERTY(id, N'IsUserTable') = 1)		
drop table [dbo].[_MKClassIds]
go

create table _MKClassIds (
	id bigint not null primary key,
	name varchar(100)
)\ngo
''')
		wr('delete from _MKClassIds\n\n')
		id = 1
		for klass in self._klasses:
			wr('insert into _MKClassIds (id, name) values\n')
			wr ('\t(%s, %r)\n' % (id, klass.name()))
			klass.setId(id)
			id += 1
		wr('\ngo\n\n')


	def writeKeyValue(self, out, key, value):
		''' Used by willWriteSQL(). '''
		key = ljust(key, 12)
		out.write('# %s = %s\n' % (key, value))

	def willWriteSQL(self, generator, out):
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
		for klass in self._klasses:
			wr('\t%s\n' % klass.name())
		wr('*/\n\n')

		sql = generator.setting('PreSQL', None)
		if sql:
			wr('/* PreSQL start */\n' + sql + '\n/* PreSQL end */\n\n')

# If database doesn't exist create it.
		dbName = generator.dbName()
		wr( 'Use Master\n' )
		wr( 'go\n\n' )
		wr( "if not exists( select * from master.dbo.sysdatabases where name = N'%s' ) create database %s; \n" % (dbName, dbName))
		wr( 'go\n\n' )
		wr('Use %s\ngo\n\n' % dbName)\
		

		rList = self._klasses[:]
		rList.reverse()
#		print str(type(rList))
#		for klass in rList:
# If table exists, then drop it.
#			wr("if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[%s]') and OBJECTPROPERTY(id, N'IsUserTable') = 1)\n" % klass.name() )
#			wr('drop table [dbo].[%s]\n' % klass.name() )
#			wr('go\n\n')
			
	def _writeSQL(self, generator, out):
		for klass in self._klasses:
			klass.writeSQL(self._sqlGenerator, out)
		self.writeClassIdsSQL(generator, out)

	def didWriteSQL(self, generator, out):
		sql = generator.setting('PostSQL', None)
		if sql:
			out.write('/* PostSQL start */\n' + sql + '\n/* PostSQL end */\n\n')
#		out.write('sp_tables\nGO\n')
		out.write('/* end of generated SQL */\n')


class Klass:

	def _writeSQL(self, generator, out):
		if not self.isAbstract():
			name = self.name()
			wr = out.write
			sqlIdName = self.sqlIdName()
			if generator.setting('DropStatements'):
# If table exists drop.
				wr ("if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[%s]') and OBJECTPROPERTY(id, N'IsUserTable') = 1)\n" % name )
				wr ('drop table [dbo].[%s]\n' % name)
				wr ('go\n\n')
# Create table.
			wr('create table [%s] (\n' % name)
			wr('	%s bigint primary key not null IDENTITY (1, 1),\n' % ljust(sqlIdName, self.maxNameWidth()))

			for attr in self.allAttrs():
				attr.writeSQL(generator, out)
				
#			wr('	unique (%s)\n' % sqlIdName)
			wr(')\ngo\n\n\n')

	def sqlIdName(self):
		name = self.name()
		if name:
			name = lower(name[0]) + name[1:] + 'Id'
		return name

	def maxNameWidth(self):
		return 30   # @@ 2000-09-15 ce: Ack! Duplicated from Attr class below


class Attr:

	def _writeSQL(self, generator, out):
		if self.hasSQLColumn():
			name = ljust(self.sqlName(), self.maxNameWidth())
			out.write('\t%s %s null,\n' % (name, self.sqlType()))
		else:
			out.write('\t/* %(Name)s %(Type)s - not a SQL column */\n' % self)

	def maxNameWidth(self):
		return 30  # @@ 2000-09-14 ce: should compute that from names rather than hard code

	def sqlType(self):
		return self['Type']
		# @@ 2000-10-18 ce: reenable this when other types are implemented
		raise SubclassResponsibilityError

class DateTimeAttr:
	def sqlType(self):
		return 'DateTime'

class DateAttr:
	def sqlType(self):
		return 'DateTime'

class TimeAttr:
	def sqlType(self):
		return 'DateTime'

class BoolAttr:

	def sqlType(self):
		# @@ 
		return 'bit'

class DecimalAttr:
	def sqlType(self):

		if not self['Max']:
			length = 11
		else:
			length = self['Max']

		if not self['numDecimalPlaces']:
			precision = 3
		else:
			precision = self['numDecimalPlaces']

		return 'decimal(%s,%s)' % (length,precision)
		

class LongAttr:

	def sqlType(self):
		# @@ 2000-10-18 ce: is this ANSI SQL?
		return 'bigint'


class StringAttr:

	def sqlType(self):
#		print 'ugh'
		if not self['Max']:
			return 'varchar(100) /* WARNING: NO LENGTH SPECIFIED */'
		elif self['Min']==self['Max']:
			return 'char(%s)' % self['Max']
		else:
			return 'varchar(%s) %s' % (self['Max'],self.get('Ref',''))

class EnumAttr:

	def sqlType(self):
		enums = ['"%s"' % enum for enum in self.enums()]
		enums = ', '.join(enums)
		enums = 'enum(%s)' % enums
		return enums

class ObjRefAttr:

	def sqlType(self):
		if self.get('Ref',None):
			return 'bigint foreign key references %(Type)s(%(Type)sID) ' % self
		else:
			return 'bigint /* relates to %s */ ' % self['Type']
		


class ListAttr:

	def sqlType(self):
		raise Exception, 'Lists do not have a SQL type.'

from SQLPythonGenerator import SQLPythonGenerator


class MSSQLPythonGenerator(SQLPythonGenerator):
	pass
	
class ObjRefAttr:

	def writePySet(self, out):
		name = self.name()
		pySetName = self.pySetName()
		targetClassName = self.className()
		if self.isRequired():
			reqAssert = 'assert value is not None'
		else:
			reqAssert = ''
		out.write('''
	def %(pySetName)s(self, value):
		%(reqAssert)s
		if value is not None and type(value) is not LongType:
			assert type(value) is InstanceType
		self._%(name)s = value
''' % locals())

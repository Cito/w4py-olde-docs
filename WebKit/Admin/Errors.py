from DumpCSV import DumpCSV

class Errors(DumpCSV):

	def filename(self):
		return self.application().setting('ErrorLogFilename')

	def cellContents(self, rowIndex, colIndex, value):
		"""This is a hook for subclasses to customize the contents of a cell based on any criteria (including location)."""
		if self._headings[colIndex] in ('pathname', 'error report filename'):
			return '<a href="file:///%s">%s</a>' % (value, value)
		else:
			return value

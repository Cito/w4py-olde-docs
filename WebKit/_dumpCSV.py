import os, string
from AdminPage import AdminPage


def LoadCSV(filename):
	''' Loads a CSV (comma-separated value) file from disk and returns it as a list of rows where each row is a list of values (which are always strings). '''

	from MiscUtils import CSV
	file = CSV.CSV()
	file.load(filename, 0, 0)
		# first  0 - first row is titles. I make this false so row[0] contains the headings
		# second 0 - convert numbers. I don't need this.
	return file

	# 2000-05-03 ce: Old code that doesn't handle quotes
	f = open(filename)
	rows = []
	numFields = None
	lineNum = 1
	while 1:
		line = f.readline()
		if not line:
			break
		rows.append(string.split(line, ','))
		if numFields is None:
			numFields = len(rows[0])
		else:
			assert len(rows[-1])<=numFields, 'Row %d has %d fields which exceeds the heading row which has %d.' % (lineNum, len(rows[-1]), numFields)
		lineNum = lineNum + 1
	f.close()
	return rows


class _dumpCSV(AdminPage):

	def awake(self, trans):
		AdminPage.awake(self, trans)
		self._filename = self.request().field('filename')

	def shortFilename(self):
		return os.path.splitext(os.path.split(self._filename)[1])[0]

	def title(self):
		return 'View ' + self.shortFilename()

	def writeBody(self):
		if not os.path.exists(self._filename):
			self.writeln('<p> File does not exist.')
			return

		rows = LoadCSV(self._filename)

		if len(rows)==1:
			plural = ''
		else:
			plural = 's'
		self.writeln('<p>%d row%s' % (len(rows), plural))
		self.writeln('<br><table align=center border=0 cellpadding=2 cellspacing=2 bgcolor=#EEEEEE>')


		# Head row gets special formatting
		self._headings = map(lambda name: string.strip(name), rows[0])
		self._numCols = len(self._headings)
		self.writeln('<tr bgcolor=black>')
		for value in self._headings:
			self.writeln('<td><font face="Arial, Helvetica" color=white><b> ', value, ' </b></font></td>')
		self.writeln('</tr>')

		# Data rows
		rowIndex = 1
		for row in rows[1:]:
			self.writeln('<tr>')
			colIndex = 0
			for value in row:
				if colIndex<self._numCols: # for those cases where a row has more columns that the header row.
					self.writeln('<td> ', self.cellContents(rowIndex, colIndex, value), ' </td>')
				colIndex = colIndex + 1
			self.writeln('</tr>')
			rowIndex = rowIndex + 1

		self.writeln('</table>')

	def cellContents(self, rowIndex, colIndex, value):
		''' This is a hook for subclasses to customize the contents of a cell based on any criteria (including location). '''
		return value

import os
from stat import ST_SIZE

print '''%s
<html>
	<head>
		<title>Webware CGI Examples Directory</title>
	</head>
	<body>
		<h1 align="center">Webware CGI Examples</h1>
''' % wrapper.docType()

def sizeSorter(a, b):
	"""Sort by size

	Used for sorting when the elements are dictionaries and the
	attribute to sort by is 'size'.

	"""
	return int(a['size'] - b['size'])

# Create a list of dictionaries, where each dictionary stores information about
# a particular script.
scripts = []
for filename in os.listdir(os.curdir):
	if len(filename) > 3 and filename[-3:] == '.py':
		script = {}
		script['pathname']  = filename
		script['size']      = os.stat(script['pathname'])[ST_SIZE]
		script['shortname'] = filename[:-3]
		scripts.append(script)
scripts.sort(sizeSorter)

print '<table cellspacing="2" cellpadding="2" align="center">'
print '<tr>',
print '<th align="right">Size</th>',
print '<th align="left">Script</th>',
print '<th align="left">View</th>',
print '</tr>'

for script in scripts:
	print '<tr>',
	print '<td align=right> %d </td>' % script['size'],
	print '<td> <a href="%s">%s</a> </td>' % (script['shortname'], script['shortname']),
	print '<td> <a href="View?filename=%s">view</a> </td>' % script['shortname'],
	print '</tr>'

print '</table>'

print '''
	</body>
</html>'''

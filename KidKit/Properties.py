name = 'KidKit'

version = ('X', 'Y', 0)

docs = [ {'name': "User's Guide", 'file': 'UsersGuide.html'} ]

status = 'alpha'

requiredPyVersion = (2, 3, 0)

requiredKidVersion = (0, 6, 4)

synopsis = """KidKit is a Webware plug-in that allows Kid templates
to be automatically compiled and run as servlets by the WebKit application server.
Kid is a simple templating language for XML based vocabularies written in Python.
You need to install the Kid package before you can use the KidKit plug-in."""

WebKitConfig = {
	'examplePages': [
		'Welcome', 'Time1', 'Time2', 'Files',
		'ServletInfo', 'SimpleForm', 'MandelbrotSet',
	]
}

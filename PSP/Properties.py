name = 'Python Server Pages'

version = (0, 4, 0)

docs = [ {'name': "User's Guide", 'file': 'UsersGuide.html'} ]

status = 'beta'

requiredPyVersion = (1, 5, 2)

synopsis = '''A Python Server Page (or PSP) is an HTML document with interspersed Python instructions that are interpreted to generate dynamic content. PSP is analogous to PHP, Microsoft's ASP and Sun's JSP. PSP sits on top of (and requires) WebKit and therefore benefits from its features.'''

WebKitConfig = {
	'examplePages': [
		'Braces',
		'Hello',
		'PSPDocs',
		'PSPTests-Braces',
		'PSPTests',
		'TrackingExample',
		'index',
		'my_include',
	],
}

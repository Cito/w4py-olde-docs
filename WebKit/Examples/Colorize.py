from Page import Page
import sys,os,string
try:
	from cStringIO import StringIO
except:
	from StringIO import StringIO

class Colorize(Page):
	"""
	Syntax highlights python source files.  Set a variable 'filename' in the request so I know which file to work on.
	This also demonstrates forwarding.  The View servlet actually forwards it's request here.
	"""

	def respond(self, transaction):
		"""
		write out a syntax hilighted version of the file.  The filename is an attribute of the request object
		"""
		res=transaction._response
		req=self.request()
		if not req.hasField('filename'):
			res.write("No filename given to syntax color!")
			return
		#filename = req.relativePath(req.field('filename')+'.py')
		filename = req.field('filename')
		if not os.path.exists(filename):
			res.write(filename+" does not exist.")
			return

		try:
			import py2html
		except:
			import imp
			modinfo=imp.find_module('py2html',["DocSupport/",])
			py2html=imp.load_module('py2html',modinfo[0],modinfo[1],modinfo[2])


		try:
			import PyFontify
		except:
			import imp
			modinfo=imp.find_module('PyFontify',["DocSupport/",])
			PyFontify=imp.load_module('PyFontify',modinfo[0],modinfo[1],modinfo[2])


		myout=StringIO()
		realout=sys.stdout
		sys.stdout=myout

		py2html.main((None,'-stdout','-format:rawhtml','-files',filename))

		results = myout.getvalue()
		results = string.replace(results, '\t', '    ')  # 4 spaces per tab
		res.write(results)

		sys.stdout=realout



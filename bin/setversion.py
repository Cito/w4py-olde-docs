#!/usr/bin/env python

"""
This script updates the version number information 
in the Properties.py files, as well as *.html and *.txt. 

	*.html files version information is updated by searching for a
	comment tag surrounding both version and release date and replacing
	the version and release date information respectively.

	*.txt files are updated matching 
		:Version:
		:Released:
	tags at the beginning of the line.  This is designed for the 
	reStructured text documents.  Note that reStructured text
	HTML files will need to be re-generated after processing.

	Properties.py files are updated, replacing the version setting
	and releaseDate setting.

When updating the HTML files, it does not update old RelNotes files,
so the tags can safely stay in the old html.

-- written by Stuart Donaldson - stu at asyn.com
"""

from glob import glob
import os,sys,re,string

progPath = os.path.abspath(sys.argv[0])  # the location of this script
webwarePath = os.path.dirname(os.path.dirname(progPath))  # because we're in Webware/bin/

sys.path.append( webwarePath )
os.chdir( webwarePath )

from MiscUtils.PropertiesObject import PropertiesObject

# format is ( Major, Minor, Sub, Alpha/Beta/etc )
# The Sub is optional, and if 0 is not returned.
# Examples include:
#   (0, 8, 1, 'b1')
#   (0, 8, 2)

# update this to change the version  and release Date 
version = ('X', 'Y', 0)
releaseDate = '@@/@@/@@'


class Replacer:
	"""
	Class to handle substitutions in a file.
	"""
	def __init__(self, *args):
		self._subs = list( args )

	def add( self, search, replace ):
		self._subs.append( (re.compile(search,re.M), replace ) )

	def replaceInStr(self, data):
		for search, replace in self._subs:
			data = re.sub( search, replace, data )
		return data

	def replaceInFile(self, filename):
		data = open(filename).read()
		newdata = self.replaceInStr( data )

		if data != newdata:
			print "Updating  %s" % filename
			open(filename,"w").write(newdata)
		else:
			print "unchanged %s" % filename

	def replaceGlob(self, pattern, skip=None):
		for file in glob(pattern):
			if skip and string.find(file,skip) >= 0:
				continue
			if os.path.exists( file ):
				self.replaceInFile( file )



po = PropertiesObject()
po.loadValues( { 'version' : version, 'releaseDate': releaseDate } )
po.createVersionString()

propReplace = Replacer()
propReplace.add( r"(version\s*=)\s*.*",  r"\g<1> %s" % repr(version) )
propReplace.add( r"(releaseDate\s*=)\s*.*", r"\g<1> %s" % repr(releaseDate) )

docReplace = Replacer()
docReplace.add( r"<!--\s*version\s*-->[^<]*<!--\s*/version\s*-->",
		r"<!-- version --> %s <!-- /version -->" % po['versionString'] )
docReplace.add( r"<!--\s*relDate\s*-->[^<]*<!--\s*/relDate\s*-->",
		r"<!-- relDate --> %s <!-- /relDate -->" % po['releaseDate'] )

rstReplace = Replacer()
rstReplace.add( r"^:Version:.*$", ":Version: %s" % po['versionString'] )
rstReplace.add( r"^:Released:.*$", ":Released: %s" % po['releaseDate'] )


def getXYZ(version):
	ver = map(lambda x: str(x), version)
	if ver[2]=='0': # e.g., if minor version is 0
		numbers = ver[:2]
	else:
		numbers = ver[:3]
	# ignore this here. rest = ver[3:]
	numbers = string.join(numbers, '.')
	return numbers


propReplace.replaceGlob( "*/Properties.py" )
propReplace.replaceGlob( "Properties.py" )


# get the X.Y.Z style version information and create
# a pattern for the RelNotes-X.Y.Z.html. 

vstr = getXYZ( version )
relnotes = "RelNotes-%s.html" % vstr

# Do not replace version information in release notes other 
# than this version.
docReplace.replaceGlob( "Docs/%s" % relnotes )
docReplace.replaceGlob( "*/Docs/%s" % relnotes )

# replace in existing HTML
docReplace.replaceGlob( "Docs/*.html", skip="RelNotes" )
docReplace.replaceGlob( "*/Docs/*.html", skip="RelNotes" )

# replace in reStructuredText files.
rstReplace.replaceGlob( "Docs/*.txt", skip="RelNotes" )
rstReplace.replaceGlob( "*/Docs/*.txt", skip="RelNotes" )

rstReplace.replaceGlob( "_README" )

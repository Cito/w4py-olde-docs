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

	ReleaseNotes-X.Y.phtml files are copied to a file with the current
	version, replacing the version and releaseDate setting.

When updating the HTML files, it does not update old RelNotes files,
so the tags can safely stay in the old html.

-- written by Stuart Donaldson - stu at asyn.com
"""

from glob import glob
import os, sys, re

progPath = os.path.abspath(sys.argv[0])  # the location of this script
webwarePath = os.path.dirname(os.path.dirname(progPath))  # because we're in Webware/bin/

sys.path.append(webwarePath)
os.chdir(webwarePath)

from MiscUtils.PropertiesObject import PropertiesObject

# format is (Major, Minor, Sub, Alpha/Beta/etc)
# The Sub is optional, and if 0 is not returned.
# Examples include:
#   (0, 8, 1, 'b1')
#   (0, 8, 2)

# Update this to change the version and release date:
version = ('X', 'Y', 0)
releaseDate = '@@/@@/@@'


class Replacer:
	"""
	Class to handle substitutions in a file.
	"""
	def __init__(self, *args):
		self._subs = list(args)

	def add(self, search, replace):
		self._subs.append((re.compile(search,re.M), replace))

	def replaceInStr(self, data):
		for search, replace in self._subs:
			data = re.sub(search, replace, data)
		return data

	def replaceInFile(self, infile, outfile=None):
		data = open(infile).read()
		newdata = self.replaceInStr(data)
		if data == newdata:
			print "Unchanged %s" % infile
		else:
			if outfile is None:
				print "Updating %s" % infile
				outfile = infile
			else:
				print "Copying %s to %s" % (infile, outfile)
				outfile = os.path.join(os.path.split(infile)[0], outfile)
			open(outfile, "w").write(newdata)

	def replaceGlob(self, pattern, outfile=None):
		for file in glob(pattern):
			if os.path.exists(file):
				self.replaceInFile(file, outfile)


po = PropertiesObject()
po.loadValues({'version': version, 'releaseDate': releaseDate})
po.createVersionString()

if po['versionString'] == 'X.Y':
	print "Please set the version."
	sys.exit(1)

propReplace = Replacer()
propReplace.add(r"(version\s*=)\s*.*",  r"\g<1> %s" % repr(version))
propReplace.add(r"(releaseDate\s*=)\s*.*", r"\g<1> %s" % repr(releaseDate))

docReplace = Replacer()
docReplace.add(r"<!--\s*version\s*-->[^<]*<!--\s*/version\s*-->",
		r"<!-- version --> %s <!-- /version -->" % po['versionString'])
docReplace.add(r"<!--\s*relDate\s*-->[^<]*<!--\s*/relDate\s*-->",
		r"<!-- relDate --> %s <!-- /relDate -->" % po['releaseDate'])

rstReplace = Replacer()
rstReplace.add(r"^:Version:.*$", ":Version: %s" % po['versionString'])
rstReplace.add(r"^:Released:.*$", ":Released: %s" % po['releaseDate'])

# replace in Properties files
propReplace.replaceGlob("*/Properties.py")
propReplace.replaceGlob("Properties.py")

# replace in existing HTML
docReplace.replaceGlob("Docs/*.html")
docReplace.replaceGlob("*/Docs/*.html")

# replace in reStructuredText files
rstReplace.replaceGlob("Docs/*.txt")
rstReplace.replaceGlob("*/Docs/*.txt")

rstReplace.replaceGlob("_README")

# replace in release notes

infile = 'RelNotes-X.Y.phtml'
outfile = infile.replace('X.Y', po['versionString'])

pytpReplace = Replacer()
pytpReplace.add(r"(<%.*)' \+ versionString \+ '(.*%>)",
		r"\g<1>%s\g<2>" % po['versionString'])
pytpReplace.add(r"<% versionString %>", po['versionString'])
pytpReplace.add(r"<% releaseDate %>", po['releaseDate'])

pytpReplace.replaceGlob("Docs/" + infile, outfile)
pytpReplace.replaceGlob("*/Docs/" + infile, outfile)

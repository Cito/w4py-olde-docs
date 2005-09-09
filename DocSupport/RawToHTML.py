"""
RawToHTML.py

This script inputs a .rawhtml file and outputs a .html file of the same base name.

The .rawhtml files are basically HTML files that can contain Python dictionaries, which get processed by this script to produce HTML in their place. That HTML could be a table, a series of bullet points, etc. and is based on the content of the dictionary.

This technique comes in handy when style sheets won't go far enought. For example, you may have several blurbs in your document that have all the same content components. Until you actually write these blurbs and experiment with their look and feel, you might not know whether you want to use <table> et al, <dd> et al or something else.

A special AutoToC dictionary can be used to automatically create a table of contents from the HTML headings.


EXAMPLES

For an example, see ../Docs/StyleGuidelines.rawhtml.


RULES

There are some rules to help this script recognize the Python dictionaries without confusing them with ordinary HTML content.

* The dictionary starts with a single curly brace on a line by itself in column 1 (e.g., no preceding white space).
* The immediate line after words starts with a single or double quote optionally preceded by white space.
* The dictionary ends with a single curly brace on a line by itself in column 1.

* htForDict() can return an string containing HTML, or a list of strings.


FUTURE

* Add a verbose option.
* Provide for the class definitions to be outside this script (in findClass()).
* Consider if this would be useful as a generate "templating" component (along with additional features).
* Consider if using one of Webware's featured templating languages (PSP, Kid) would be a better idea.
* Consider if using something like ReST, AsciiDoc would be a better idea.

"""


import os, sys, re
from glob import glob
from types import *


class Convention:
	"""
	"Raw to HTML" class specifically for ../Docs/StyleGuidelines.rawhtml.
	"""

	def __init__(self, processor):
		pass

	def htForDict(self, dict):
		self._dict = dict
		self._results = []
		for key in ['what', 'why', 'examples', 'negatives', 'exceptions']:
			self.part(key)
		return self._results

	def part(self, key):
		if self._dict.has_key(key):
			value = self._dict[key]
			if key in ('examples', 'negatives', 'exceptions'):
				if key != 'exceptions':
					value = ('\n' in value and '<pre class="py">%s</pre>'
						or '<code>%s</code>') % value
				value = '%s: %s' % (key.capitalize(), value)
			self._results.append('<div class="%s">%s</div>' % (key, value))


class AutoToC:
	"""
	"Raw to HTML" class for automatic table of contents.
	"""

	toc = 0
	title = None
	headings = []

	def __init__(self, processor):
		pass

	def htForDict(self, dict):
		if dict.has_key('title'):
			AutoToC.title = dict['title']
		else:
			AutoToC.title= 'Table of Contents'
		AutoToC. toc += 1
		return '%(AutoToC.toc)s'


class RawToHTML:

	def __init__(self):
		self._translators = {}

	def main(self, args):
		for filename in args[1:]:
			if '*' in filename:
				# Help out Windows command line users
				filenames = glob(filename)
				for filename in filenames:
					self.processFile(filename)
			else:
				self.processFile(filename)

	def error(self, msg):
		# @@ 2000-10-08 ce: raise an exception
		print msg
		sys.exit(1)

	def createTranslator(self, className):
		""" Returns a translator by instantiating a class for the given name out of globals(). A subclass could override this (or a future version of this class could change this) to do something more sophisticated, like locate the class in the current directory or DocSupport. Used by processString(). """
		pyClass = globals()[className]
		return pyClass(self)

	def translator(self, className):
		""" Returns the translator for the given class name, invoking createTranslator() if necessary. """
		translator = self._translators.get(className, None)
		if translator is None:
			translator = self.createTranslator(className)
			self._translators[className] = translator
		return translator

	def processFile(self, filename):
		targetName = os.path.splitext(filename)[0] + '.html'
		contents = open(filename).read()
		results = self.processString(contents)
		open(targetName, 'w').write(results)

	def processString(self, contents):
		lines = contents.splitlines()
		numLines = len(lines)
		i = 0
		results = []
		pattern_heading = re.compile('<h[1-6]>.*</h[1-6]>', re.IGNORECASE)
		while i<numLines:
			line = lines[i]
			if line.strip()=='{':
				start = i
				while 1:
					i = i + 1
					if i==numLines:
						self.error('Unterminated Python dictionary starting at line %d.' % (start+1))
					line = lines[i]
					if line.strip()=='}':
						end = i
						break
				dictString = '\n'.join(lines[start:end+1])
				try:
					dict = eval(dictString)
				except:
					self.error('Could not evaluate dictionary starting at line %d.' % (start+1))
				translator = self.translator(dict['class'])
				ht = translator.htForDict(dict)
				if type(ht)==ListType:
					results.extend(ht)
				else:
					results.append(ht)
			elif pattern_heading.search(line):
				results.append('%%(AutoToC.headings[%d])s' % len(AutoToC.headings))
				AutoToC.headings.append(line)
			else:
				results.append(line)
			i += 1
		# additional processing for table of contentes
		pattern_heading = re.compile('<h([1-6])>(.*)</h[1-6]>', re.IGNORECASE)
		pattern_label = re.compile('<a name="(.*)">', re.IGNORECASE)
		headings = [(int(g[0]), g[1])
			for g in [pattern_heading.search(heading).groups()
			for heading in AutoToC.headings]]
		minLevel = None
		for level in range(1,7):
			if len([headings[0] for heading in headings if heading[0]==level])>1:
				minLevel = level
				break
		else:
			minLevel = None
		if minLevel:
			toc = ['<div class="ToC">']
			if AutoToC.title:
				toc.append('\n<h%d>%s</h%d>' % (minLevel, AutoToC.title, minLevel))
			level = minLevel-1
			num = [0] * 6
			i = 0
			for heading in headings:
				if heading[0]>=minLevel:
					if level>=heading[0]:
						if num[level-minLevel]:
							toc.append('</li>')
						while level>heading[0]:
							toc.append('</ul></li>')
							num[level-minLevel] = 0
							level -= 1
						num[level-minLevel] += 1
						toc.append('\n<li>')
					else:
						while level<heading[0]:
							toc.append('<ul>\n<li>')
							level += 1
							num[level-minLevel] += 1
					label = pattern_label.search(AutoToC.headings[i])
					if label:
						label = label.group(1)
					else:
						label = '.'.join(map(str, num[:level-minLevel+1]))
						AutoToC.headings[i] = '<a name="%s"></a>%s' % (label, AutoToC.headings[i])
					toc.append('<a href="#%s">%s</a>' % (label, heading[1]))
				i += 1
			while level>=minLevel:
				toc.append('</li></ul>')
				level -= 1
			toc.append('\n</div>')
			toc = ''.join(toc)
		else:
			toc = None
		numLines = len(results)
		i = 0
		while i<numLines:
			line = results[i]
			if line.startswith('%(AutoToC.') and line.endswith(')s'):
				line = line[10:-2]
				if line.startswith('headings[') and line.endswith(']'):
					line = AutoToC.headings[int(line[9:-1])]
					results[i] = line
				elif line=='toc':
					if toc:
						results[i] = toc
					else:
						del results[i]
						i -= 1
			i += 1
		return '\n'.join(results)


if __name__=='__main__':
	RawToHTML().main(sys.argv)

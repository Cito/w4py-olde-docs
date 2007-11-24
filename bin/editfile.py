#!/usr/bin/env python

# Helper script for the feature provided by the IncludeEditLink setting.

editor = 'gnuclient (Emacs)'

editorCommands = {
	'gnuclient (Emacs)':
		'gnuclient +%(line)s %(filename)s',
	'Geany (Windows)':
		r'start %%ProgramFiles%%\Geany\Geany.exe -l %(line)s "%(filename)s"',
	'PSPad (Windows)':
		r'start %%ProgramFiles%%\PSPad\PSPad.exe -%(line)s "%(filename)s"',
	'SciTE (Windows)':
		r'start %%ProgramFiles%%\SciTE\SciTE.exe "%(filename)s" -goto:%(line)s',
	}

from os import system
from sys import argv
try:
	from email import message_from_file
except ImportError:
	from rfc822 import Message as message_from_file

def openFile(params):
	command = editorCommands[editor] % params
	system(command)

def parseFile(filename):
	file = open(filename)
	openFile(message_from_file(file))

if __name__ == '__main__':
	parseFile(argv[1])

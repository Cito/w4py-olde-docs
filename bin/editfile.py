#!/usr/bin/env python

# Helper script for the feature provided by the IncludeEditLink setting.

editor = 'Vim'

editorCommands = {
	'Emacs':
		'gnuclient +%(line)s "%(filename)s"',
	'Geany':
		'geany -l %(line)s "%(filename)s"',
	'Geany (Windows)':
		r'start %%ProgramFiles%%\Geany\Geany.exe -l %(line)s "%(filename)s"',
	'gedit':
		'gedit +%(line)s "%(filename)s"',
	'jEdit':
		'jedit "%(filename)s" +line:%(line)s',
	'Kate':
		'kate -u -l %(line)s "%(filename)s"',
	'KWrite':
		'kwrite --line %(line)s "%(filename)s"',
	'Pico':
		'pico +%(line)s "%(filename)s"',
	'PSPad (Windows)':
		r'start %%ProgramFiles%%\PSPad\PSPad.exe -%(line)s "%(filename)s"',
	'SciTE':
		'scite "%(filename)s" -goto:%(line)s',
	'SciTE (Windows)':
		r'start %%ProgramFiles%%\SciTE\SciTE.exe "%(filename)s" -goto:%(line)s',
	'Vim':
		'gvim +%(line)s "%(filename)s"',
	}

defaultCommand = editor + ' +%(line)s "%(filename)s"'

from os import system
from sys import argv
try:
	from email import message_from_file
except ImportError:
	from rfc822 import Message as message_from_file

def openFile(params):
	command = editorCommands.get(editor, defaultCommand) % params
	system(command)

def parseFile(filename):
	file = open(filename)
	openFile(message_from_file(file))

if __name__ == '__main__':
	parseFile(argv[1])

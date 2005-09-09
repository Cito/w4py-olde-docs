#!/usr/bin/env python
#
# Clean up Webware installation directory
# (remove all derived and temporary files).
# This will work with all operating systems.
#

# Files that shall be removed:

files = '''
*~
*.bak
*.pyc
*.pyo
CGIWrapper/Errors.csv
CGIWrapper/Scripts.csv
CGIWrapper/ErrorMsgs/*.html
WebKit/address.text
WebKit/Logs/*.csv
WebKit/ErrorMsgs/*.html
'''

import os, glob

def remove(pattern):
	for name in glob.glob(pattern):
		os.remove(name)

def walk_remove(pattern, dirname, names):
	pattern = os.path.join(dirname, pattern)
	remove(pattern)

print "Cleaning up..."

for pattern in files.splitlines():
	if pattern:
		print pattern
		if '/' in pattern:
			remove(pattern)
		else:
			os.path.walk('.', walk_remove, pattern)

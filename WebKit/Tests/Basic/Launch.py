#!/usr/bin/python

import os, sys

os.chdir(os.path.abspath(os.path.dirname(__file__)))
webwareDir = os.path.join(os.pardir, os.pardir, os.pardir)
sys.path.insert(0, webwareDir)

from WebKit import Launch

Launch.webwareDir = webwareDir

if __name__ == '__main__':
	Launch.main()

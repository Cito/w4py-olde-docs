#!/usr/bin/env python

# If the Webware installation is located somewhere else,
# then set the webwareDir variable to point to it here:
WebwareDir = None

# If you used the MakeAppWorkDir.py script to make a separate
# application working directory, specify it here:
workDir = None

try:
	import os, sys
	if not WebwareDir:
		WebwareDir = os.path.dirname(os.path.dirname(os.getcwd()))
	sys.path.insert(1, WebwareDir)
	webKitDir = os.path.join(WebwareDir, 'WebKit')
	if workDir is None:
		workDir = webKitDir
	else:
		sys.path.insert(1, workDir)
	import WebKit.Adapters.OneShotAdapter
	WebKit.Adapters.OneShotAdapter.main(workDir)
except:
	import sys, traceback
	from time import asctime, localtime, time
	sys.stderr.write('[%s] [error] WebKit: Error in adapter\n' % asctime(localtime(time())))
	sys.stderr.write('Error while executing script\n')
	traceback.print_exc(file=sys.stderr)
	output = ''.join(traceback.format_exception(*sys.exc_info()))
	output = output.replace('&', '&amp;').replace(
		'<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
	sys.stdout.write('''Content-type: text/html\n
<html><head><title>WebKit CGI Error</title><body>
<h3>WebKit CGI Error</h3>
<pre>%s</pre>
</body></html>\n''' % output)

#!/usr/bin/env python

# If the WebKit installation is located somewhere else,
# then set the WebKitDir variable to point to it.
# For example, WebKitDir = '/Servers/Webware/WebKit'
WebKitDir = None

try:
	if WebKitDir:
		import os, sys
		os.chdir(WebKitDir)
		sys.path.insert(0, '.')
	import OneShotAdapter
	OneShotAdapter.main()
except:
	import string, sys, traceback
	from time import asctime, localtime, time

	sys.stderr.write('[%s] [error] WebKit: Error in adapter\n' % asctime(localtime(time())))
	sys.stderr.write('Error while executing script\n')
	traceback.print_exc(file=sys.stderr)

	output = apply(traceback.format_exception, sys.exc_info())
	output = string.join(output, '')
	output = string.replace(output, '&', '&amp;')
	output = string.replace(output, '<', '&lt;')
	output = string.replace(output, '>', '&gt;')
	output = string.replace(output, '&', '&quot;')
	sys.stdout.write('''Content-type: text/html

<html><body>
<p>ERROR
<p><pre>%s</pre>
</body></html>\n''' % output)


#!python

# If the Webware installation is located somewhere else,
# then set the WebwareDir variable to point to it.
# For example, WebwareDir = '/Servers/Webware'
WebwareDir = None

try:
	import os, sys
	if WebwareDir:
		sys.path.insert(1, WebwareDir)
	else:
		WebwareDir = os.path.dirname(os.getcwd())
	webKitDir = os.path.join(WebwareDir, 'WebKit')
	import WebKit.CGIAdapter
	WebKit.CGIAdapter.main(webKitDir)
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
	output = string.replace(output, '"', '&quot;')
	sys.stdout.write('''Content-type: text/html

<html><body>
<p>ERROR
<p><pre>%s</pre>
</body></html>\n''' % output)

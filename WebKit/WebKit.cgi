#!/usr/bin/env python

try:
	import CGIAdaptor
	CGIAdaptor.main()
except:
	import string, sys, traceback
	from time import asctime, localtime, time
		
	sys.stderr.write('[%s] [error] WebKit: Error in adaptor\n' % asctime(localtime(time())))
	sys.stderr.write('Error while executing script\n')
	traceback.print_exc(file=sys.stderr)
		
	output = apply(traceback.format_exception, sys.exc_info())
	output = string.join(output, '')
	output = string.replace(output, '&', '&amp;')
	output = string.replace(output, '<', '&lt;')
	output = string.replace(output, '>', '&gt;')
	sys.stdout.write('''Content-type: text/html

<html><body>
<p>ERROR
<p><pre>%s</pre>
</body></html>\n''' % output)

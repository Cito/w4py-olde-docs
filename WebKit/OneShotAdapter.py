'''
OneShotAdapter.py

This is a special version of the CGIAdapter that doesn't require a persistent AppServer process. This is mostly useful during development when repeated changes to classes forces the developer to restart the app server to make the changes take effect.

An example, URL:

	http://127.0.0.1/OneShot.cgi/MyPage

'''


import time
timestamp = time.time()

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO


# @@ 2000-07-10 ce fix this up
import sys
sys.path.append('..')
import WebUtils
from WebUtils.WebFuncs import HTMLEncode


def main():
	import os, string, sys

	try:
		myInput = sys.stdin.read()

		dict = {
			'format':  'CGI',
			'time':    timestamp,
			'environ': os.environ.data, # ce: a little tricky. We use marshal which only works on built-in types, so we need environ's dictionary
			'input':   myInput
		}

		real_stdout = sys.stdout
		sys.stdout = console = StringIO()  # to capture the console output of the application
		print 'ONE SHOT MODE\n'

		from OneShotAppServer import OneShotAppServer
		appSvr = OneShotAppServer()
		response = appSvr.dispatchRawRequest(dict).response().rawResponse()
		appSvr.shutDown()
		appSvr = None

		sys.stdout = real_stdout
		if os.name=='nt': # MS Windows: no special translation of end-of-lines
			import msvcrt
			msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
		write = sys.stdout.write
		for pair in response['headers']:
			write('%s: %s\n' % pair)
		write('\n')
		write(response['contents'])
		write('<br><p><table><tr><td bgcolor=#EEEEEE><pre>%s</pre></td></tr></table>' % HTMLEncode(console.getvalue()))
	except:
		import traceback

		sys.stderr.write('[%s] [error] WebKitCGIAdaptor: Error while responding to request (unknown)\n' % (
			time.asctime(time.localtime(time.time()))))
		sys.stderr.write('Python exception:\n')
		traceback.print_exc(file=sys.stderr)

		output = apply(traceback.format_exception, sys.exc_info())
		output = string.join(output, '')
		output = string.replace(output, '&', '&amp;')
		output = string.replace(output, '<', '&lt;')
		output = string.replace(output, '>', '&gt;')
		output = string.replace(output, '"', '&quot;')
		sys.stdout.write('''Content-type: text/html

<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)


if __name__=='__main__':
	main()

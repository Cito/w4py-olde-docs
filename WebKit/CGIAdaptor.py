'''
CGIAdapator.py

This is the CGI Adaptor for the WebKit AppServer.

This CGI script collects information about the request, puts it into a
package, and then sends it to the WebKit application server over TCP/IP.

This script expects to find a file in it's directory called
'address.text' that specifies the address of the app server.
The file is written by the app server upon successful startup
and contains nothing but:

hostname:port

with no other characters, not even a newline. For example,

localhost:8086

or even:

:8086

...since an empty string is a special case indicating the local host.

'''


import time
timestamp = time.time()

from socket import *
from marshal import dumps


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

		# 2000-05-20 ce: For use in collecting raw request dictionaries for use in Testing/stress.py
		# Leave this code here in case it's needed again
		#
		#counter = int(open('counter.text').read())
		#counter = counter + 1
		#open('counter.text', 'w').write(str(counter))		
		#open('rr-%02d.rr' % counter, 'w').write(str(dict))

		(host, port) = string.split(open('address.text').read(), ':')
		port = int(port)
		bufsize = 32*1024  # @@ 2000-04-26 ce: this should be configurable, also we should run some tests on different sizes
		
		s = socket(AF_INET, SOCK_STREAM)
		s.connect(host, port)
		s.send(dumps(dict))
		s.shutdown(1)
		while 1:
			data = s.recv(bufsize)
			if not data:
				break
			sys.stdout.write(data)

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
		sys.stdout.write('''Content-type: text/html

<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)


if __name__=='__main__':
	main()

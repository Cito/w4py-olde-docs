#!/usr/bin/env python

"""
FCGIAdapator.py

FCGI Adaptor for the WebKit application environment.

This script is started by the Web Server and is kept running.
When a request comes through here, this script collects information
about the request, puts it into a package, and then invokes the
WebKit Application to handle it.

Original CGI implementaion by Chuck Esterbrook.

FastCGI Implementation by Jay Love. Based on threaded fcgi example "sz_fcgi" provided by "Andreas Jung"



SETUP

To use this adaptor, you must have a fastcgi capable web server.

For Apache, you'll need to add the following lines to your httpd.conf file, or
put them in another file and include that file in httpd.conf

#I have the file in my cgi-bin directory, but you might as well put it in html.
#the -host is the port it communicates on
FastCgiExternalServer ../cgi-bin/FCGIWebKit.py -host localhost:33333 # the path is from the SERVER ROOT

<Location /FCGIWebKit.py>  #or whatever name you chose for the file above
 SetHandler fastcgi-script
 Options ExecCGI FollowSymLinks
</Location>


You could also take an extension oriented approach in Apache using '.fcgi':

	AddHandler fastcgi-script fcgi


And then using, in your URLs, 'WebKit.fcgi' which is a link to this file. e.g.,:

	http://localhost/Webware/WebKit/WebKit.fcgi/Introspect

	

FUTURE

(*) There are some interesting lines at the top of fcgi.py:

# Set various FastCGI constants
# Maximum number of requests that can be handled
FCGI_MAX_REQS=1
FCGI_MAX_CONNS = 1

# Boolean: can this application multiplex connections?
FCGI_MPXS_CONNS=0

Do these need to be adjusted in order to realize the full benefits of FastCGI?

(*) Has anyone measured the performance difference between CGIAdaptor and FCGIAdaptor? What are the results?



CHANGES

* 2000-05-08 ce:
	* Fixed bug in exception handler to send first message to stderr, instead of stdout
	* Uncommented the line for reading 'address.text'
	* Switched from eval() encoding to marshal.dumps() encoding in accordance with AppServer
	* Increased rec buffer size from 8KB to 32KB
	* Removed use of pr() for feeding app server results back to webserver. Figure that's slightly more efficient.
	* Added notes about how I set this up with Apache to what was already there.
"""

import fcgi, time
from marshal import dumps
from socket import *

timestamp = time.time()

"""Set WebKitDir to the directory where WebKit is located"""
WebKitDir = ''

_AddressFile='address.text'


def FCGICallback(fcg,env,form):
	"""This function is called whenever a request comes in"""
	import os, string, sys

	try:
				
		dict = {
			'format':  'CGI',
			'time':    timestamp,
			'environ': env,
			'input':   form
		}

		addrfile=os.path.join(WebKitDir, _AddressFile)
		(host, port) = string.split(open(addrfile).read(), ':')
		port = int(port)

		bufsize = 32*1024
		
		s = socket(AF_INET, SOCK_STREAM)
		s.connect(host, port)
		s.send(dumps(dict))
		s.shutdown(1)
		stdout = fcg.req.out
		while 1:
			data = s.recv(bufsize)
			if not data:
				break
			stdout.write(data)
		stdout.flush()

	except:
		import traceback
		
		# Log the problem to stderr
		stderr = fcg.req.err
		stderr.write('[%s] [error] WebKitFCGIAdaptor: Error while responding to request (unknown)\n' % (
			time.asctime(time.localtime(time.time()))))
		stderr.write('Python exception:\n')
		traceback.print_exc(file=stderr)
		
		# Report the problem to the browser
		output = apply(traceback.format_exception, sys.exc_info())
		output = string.join(output, '')
		output = string.replace(output, '&', '&amp;')
		output = string.replace(output, '<', '&lt;')
		output = string.replace(output, '>', '&gt;')
		fcg.pr('''Content-type: text/html

<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)
	fcg.finish()
	return


class WKFCGI:
	"""This class handles calls from the web server"""
	def __init__(self,func):
		self.func=func

	def run(self):
		"""Block waiting for new request"""
		while fcgi.isFCGI():
			req=fcgi.FCGI()
			self.req=req
			self.func(self,req.env,str(req.inp))

	#easy print function
	def pr(self,*args):
		"""just a quick and easy print function"""
		try:
			req=self.req
			s=''
			for i in args: s=s+str(i)
			req.out.write(s+'\n')
			req.out.flush()
		except:
			pass


	def finish(self):
	    """Finish and send all data back to the FCGI parent"""
	    self.req.Finish()


fcgiloop = WKFCGI(FCGICallback)
fcgiloop.run()

if __name__=='__main__':
	print 'You can\'t call this from the command-line'

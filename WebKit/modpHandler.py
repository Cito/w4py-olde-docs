###########################################
# mod_python adapter for WebKit
# 
#
# Contributed by: Dave Wallace
# Modified by Jay Love
#
##########################################

"""
Here's how I set up my Apache conf:

<Location /wpy >
	SetHandler python-program
   # add the directory that contains modpHandler.py
	PythonPath "sys.path+['/path/to/WebKit']"
   PythonHandler modpHandler
   PythonDebug
</Location>

Make sure you set WEBWARE_ADDRESS_FILE below and now you can access
your running AppServer with:

http://localhost/wpy/Welcome


You may also send all requests with a .psp extension to WebKit by adding these lines, outside
of any location or dircetory.

AddHandler python-program .psp
PythonPath "sys.path+['/path/to/WebKit']"
PythonHandler modpHandler::pspHandler

"""

from mod_python import apache
import time

from socket import *
from marshal import dumps
from marshal import loads
import sys
import string

debug=0

host = None
port = None
bufsize = 32*1024

WEBWARE_ADDRESS_FILE='/data/Linux/python/Webware/WebKit/address.text'


if not port:
	(host, port) = string.split(open(WEBWARE_ADDRESS_FILE).read(), ':')
	port = int(port)

def handler(req):
	global host
	global port

	if debug:
		ot = open("/tmp/log2.txt","a")
		ot.write("req.path_info=%s\n"%req.path_info)
	try:

		timestamp = time.time()
		myInput = ""
		inp = req.read(bufsize)
		# this looks like bad performance if we don't get it all
		#  in the first buffer
		while inp:
			myInput = myInput + inp
			inp = req.read(bufsize)

		if debug:
			ot.write("*************\n%s\n************\n"% len(myInput))
			for name in req.headers_in.keys():
				ot.write("%s=%s\n"%(name,req.headers_in[name]))
			ot.write(req.uri)
			ot.write("\n*************************\n")

		# get the apache module to do the grunt work of
		#   building the environment
		env=apache.build_cgi_env(req)
		
##		WK_URI = env['REQUEST_URI'][len(env['SCRIPT_NAME']):]
##		WK_URI = env['SCRIPT_URL'][len(env['SCRIPT_NAME']):]
##		env['PATH_INFO'] = WK_URI  #Hack to accomodate the current cgi-centric approach WK uses to find the path
##		env['WK_URI'] = WK_URI
##		if env["WK_URI"] == "": env["WK_URI"]="/"
		if debug: ot.write("PATH_INFO=%s\n"% env.get('PATH_INFO'))
		if not env.has_key('PATH_INFO'): env['PATH_INFO']=req.path_info #"/"

		dict = {
				'format': 'CGI',
				'time':   timestamp,
				'environ': env,
				'input':   myInput
				}


		s = socket(AF_INET, SOCK_STREAM)
		s.connect((host, port))
		s.send(dumps(dict))
		s.shutdown(1)

		#
		# Get the response from the AppServer, extract the headers,
		#  and send everything to Apache through mod_python's req object
		#
		inheader=1
		header = ""
		resp = ''
		while 1:
			data = s.recv(bufsize)
			if not data:
				break
			resp = resp+data

		respdict = loads(resp)
		for pair in respdict['headers']:
			req.headers_out[pair[0]] = str(pair[1])
		req.content_type = req.headers_out['content-type']
		if req.headers_out.has_key('status'):
			req.status = int(req.headers_out['status'])
		req.send_http_header()
		req.write(respdict['contents'])


		if debug:
			ot.write("+++\n\n")
			ot.close()


	except:
		import traceback

		apache.log_error('WebKit mod_python: Error while responding to request\n')
		apache.log_error('Python exception:\n')
		traceback.print_exc(file=sys.stderr)
		
		output = apply(traceback.format_exception, sys.exc_info())
		output = string.join(output, '')
		output = string.replace(output, '&', '&amp;')
		output = string.replace(output, '<', '&lt;')
		output = string.replace(output, '>', '&gt;')
		req.write('''
<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)

	return apache.OK






def pspHandler(req):
	global host
	global port

	if debug:
		ot = open("/tmp/log2.txt","a")
		ot.write("req.path_info=%s\n"%req.path_info)
	try:
		if not port:
			(host, port) = string.split(open(WEBWARE_ADDRESS_FILE).read(), ':')
			port = int(port)
		
		timestamp = time.time()
		myInput = ""
		inp = req.read(bufsize)
		# this looks like bad performance if we don't get it all
		#  in the first buffer
		while inp:
			myInput = myInput + inp
			inp = req.read(bufsize)

		if debug:
			ot.write("*************\n%s\n************\n"% len(myInput))
			for name in req.headers_in.keys():
				ot.write("%s=%s\n"%(name,req.headers_in[name]))
				ot.write("*************************\n")
				ot.write(req.uri)
				ot.write("\n")

		# get the apache module to do the grunt work of
		#   building the environment
		env=apache.build_cgi_env(req)
		env['WK_ABSOLUTE']=1
		if debug:
			ot.write("%s"%env)
		#fix PATH_INFO
##		if not env.has_key('PATH_INFO'):
##			env['PATH_INFO']='/'

		dict = {
				'format': 'CGI',
				'time':   timestamp,
				'environ': env,
				'input':   myInput
				}


		s = socket(AF_INET, SOCK_STREAM)
		s.connect((host, port))
		s.send(dumps(dict))
		s.shutdown(1)

		#
		# Get the response from the AppServer, extract the headers,
		#  and send everything to Apache through mod_python's req object
		#
		inheader=1
		header = ""
		resp = ''
		while 1:
			data = s.recv(bufsize)
			if not data:
				break
			resp = resp+data

		respdict = loads(resp)
		for pair in respdict['headers']:
			req.headers_out[pair[0]] = str(pair[1])
		req.content_type = req.headers_out['content-type']
		if req.headers_out.has_key('status'):
			req.status = int(req.headers_out['status'])
		req.send_http_header()
		req.write(respdict['contents'])


		if debug:
			ot.write("+++\n\n")
			ot.close()


	except:
		import traceback

		apache.log_error('WebKit mod_python: Error while responding to request\n')
		apache.log_error('Python exception:\n')
		traceback.print_exc(file=sys.stderr)
		
		output = apply(traceback.format_exception, sys.exc_info())
		output = string.join(output, '')
		output = string.replace(output, '&', '&amp;')
		output = string.replace(output, '<', '&lt;')
		output = string.replace(output, '>', '&gt;')
		req.write('''
<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)

	return apache.OK












import string

def typehandler(req):
	""" Not being used yet.
	Probably never be used, b/c the req.handler field is read only."""
	debug=1
	if debug:
		ot = open("/tmp/log2.txt","a")
		ot.write("In Type Handler\n")
		ot.flush()

	if req.filename == None:
		return apache.DECLINED
	fn = req.filename
	if debug:
		ot.write("TH: Filename: %s\n"%fn)
	ext = fn[string.rfind(fn,"."):]
	if debug:
		ot.write("TH: Extension: %s\n"%ext)

	if debug:
		ot.write("Req_Handler = %s\n"%req.handler)
		ot.flush()
		ot.close()

	if ext == ".psp":
		req.handler = "python-program"
		return apache.OK
	else:
		return apache.DECLINED



	

#!/usr/bin/env python
## HTTPAdapter 0.0
## Serves HTTP, connecting to the Webware AppServer
## Ian Bicking <ianb@colorstudy.com>, 10 Apr 2002
##
## Modified by gtalvola 18 May 2002 to add multi-threading
## and to disallow a missing content-length on a POST
## request

# If the Webware installation is located somewhere else,
# then set the WebwareDir variable to point to it.
# For example, WebwareDir = '/Servers/Webware'
WebwareDir = '/home/gtalvola/cvs_staging/Webware'

# If you used the MakeAppWorkDir.py script to make a separate
# application working directory, specify it here.
AppWorkDir = None

# The address (?) and port that the server will serve
ServerAddress = ('', 8080)

try:
	import os, sys, string
	if WebwareDir:
		sys.path.insert(1, WebwareDir)
	else:
		WebwareDir = os.path.dirname(os.getcwd())
	webKitDir = os.path.join(WebwareDir, 'WebKit')
	if AppWorkDir is None:
		AppWorkDir = webKitDir
	else:
		sys.path.insert(1, AppWorkDir)

	from WebKit import Adapter
        (host, port) = string.split(open(os.path.join(webKitDir, 'address.text')).read(), ':')
        if os.name=='nt' and host=='': # MS Windows doesn't like a blank host name
            host = 'localhost'
        port = int(port)
except 0:
    ## @@: Is there something we should do with exceptions here?
    ## I'm apt to just let them print to stderr and quit like normal,
    ## but I'm not sure.
    pass


import BaseHTTPServer, mimetools
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import threading, socket

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler, Adapter.Adapter):
    """Handles incoming requests.  Recreated with every request."""

    ## This sends certain CGI variables.  These are some that
    ## should be sent, but aren't:
    ## SERVER_ADDR
    ## SERVER_PORT
    ## SERVER_SOFTWARE
    ## SERVER_NAME
    ## HTTP_CONNECTION
    ## SERVER_PROTOCOL
    ## HTTP_KEEP_ALIVE

    ## These I don't think are needed:
    ## DOCUMENT_ROOT
    ## PATH_TRANSLATED
    ## GATEWAY_INTERFACE
    ## PATH
    ## SERVER_SIGNATURE
    ## SCRIPT_NAME (?)
    ## SCRIPT_FILENAME (?)
    ## SERVER_ADMIN (?)

    def __init__(self, *vars):
        Adapter.Adapter.__init__(self, webKitDir)
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *vars)

    def do_GET(self):
        self.requestMethod = 'GET'
        self.doRequest()

    def do_POST(self):
        self.requestMethod = 'POST'
        self.doRequest()

    def do_HEAD(self):
        self.requestMethod = 'HEAD'
        self.doRequest()

    def doRequest(self):
        self.server_version = 'Webware/0.0'
        env = {}
        if self.headers.has_key('Content-Type'):
            env['CONTENT_TYPE'] = self.headers['Content-Type']
            del self.headers['Content-Type']
        self.headersToEnviron(self.headers, env)
        env['REMOTE_ADDR'], env['REMOTE_PORT'] = map(str, self.client_address)
        env['REQUEST_METHOD'] = self.requestMethod
        path = self.path
        if path.find('?') != -1:
            env['REQUEST_URI'], env['QUERY_STRING'] = path.split('?', 1)
        else:
            env['REQUEST_URI'] = path
            env['QUERY_STRING'] = ''
        env['PATH_INFO'] = env['REQUEST_URI']
        myInput = ''
        if self.headers.has_key('Content-Length'):
            myInput = self.rfile.read(int(self.headers['Content-Length']))
        self.transactWithAppServer(env, myInput, host, port)

    def headersToEnviron(self, headers, env):
        """Use a simple heuristic to convert all the headers to
        environmental variables..."""
        for header, value in headers.items():
            env['HTTP_%s' % (header.upper().replace('-', '_'))] = value
        return env

    def processResponse(self, data):
        s = StringIO(data)
        headers = mimetools.Message(s)
        self.doLocation(headers)
        self.sendStatus(headers)
        self.sendHeaders(headers)
        self.sendBody(s)

    def doLocation(self, headers):
        """If there's a Location header and no Status header,
        we need to add a Status header ourselves."""
        if headers.has_key('Location'):
            if not headers.has_key('Status'):
                ## @@: is this the right status header?
                headers['Status'] = '301 Moved Temporarily'

    def sendStatus(self, headers):
        if not headers.has_key('Status'):
            status = "200 OK"
        else:
            status = headers['Status']
            del headers['Status']
        pos = status.find(' ')
        if pos == -1:
            code = int(status)
            message = ''
        else:
            code = int(status[:pos])
            message = status[pos:].strip()
        self.send_response(code, message)

    def sendHeaders(self, headers):
        for header, value in headers.items():
            self.send_header(header, value)
        self.end_headers()

    def sendBody(self, bodyFile):
        self.wfile.write(bodyFile.read())
        bodyFile.close()


class ThreadedHTTPServer(BaseHTTPServer.HTTPServer):
    """
    Stolen from a 2001 comp.lang.python post by Michael Abbott.
    """
    def handle_request(self):
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        threading.Thread(target=self.handle_request_body,
                         args=(request, client_address)).start()

    # This part of the processing is run in its own thread
    def handle_request_body(self, request, client_address):
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
        self.close_request(request)

def run():
    httpd = ThreadedHTTPServer(ServerAddress, HTTPHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    if len(sys.argv) > 1 and \
       sys.argv[1] == 'daemon':
        if os.fork() or os.fork():
            sys.exit(0)
    run()

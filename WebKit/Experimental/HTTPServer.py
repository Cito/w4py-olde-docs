import BaseHTTPServer, mimetools
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import threading, socket

class HaltServer(Exception): pass

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
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

    def doRequest(self):
        self.server_version = 'Webware/0.1'
        env = {}
        if self.headers.has_key('Content-Type'):
            env['CONTENT_TYPE'] = self.headers['Content-Type']
            del self.headers['Content-Type']
        self.headersToEnviron(self.headers, env)
        env['REMOTE_ADDR'], env['REMOTE_PORT'] = map(str, self.client_address)
        env['REQUEST_METHOD'] = self.command
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
	self.doTransaction(env, myInput)

    do_GET = do_POST = do_HEAD = doRequest
    

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

    def __init__(self, *args):
        self._threads = {}
	self._threadID = 1
	BaseHTTPServer.HTTPServer.__init__(self, *args)

    def handle_request(self):
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        t = threading.Thread(target=self.handle_request_body,
                         args=(request, client_address, self._threadID))
	t.start()
	self._threads[self._threadID] = t
	self._threadID += 1
	
    # This part of the processing is run in its own thread
    def handle_request_body(self, request, client_address, threadID):
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
        self.close_request(request)
	del self._threads[threadID]

    def serve_forever(self):
        self._keepGoing = 1
	while self._keepGoing:
	    self.handle_request()
	self.socket.close()

    def shutDown(self):
        self._keepGoing = 0
	for thread in self._threads.values():
	    thread.join()
	self.socket.shutdown(2)
	self.socket.close()


def run(serverAddress, klass=HTTPHandler):
    httpd = ThreadedHTTPServer(serverAddress, klass)
    try:
        httpd.serve_forever()
    except HaltServer:
        pass

if __name__ == '__main__':
    if len(sys.argv) > 1 and \
       sys.argv[1] == 'daemon':
        if os.fork() or os.fork():
            sys.exit(0)
    run()

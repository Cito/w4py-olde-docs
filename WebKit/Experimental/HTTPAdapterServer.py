#!/usr/bin/env python
# If the Webware installation is located somewhere else,
# then set the WebwareDir variable to point to it.
# For example, WebwareDir = '/Servers/Webware'
WebwareDir = None

# If you used the MakeAppWorkDir.py script to make a separate
# application working directory, specify it here.
AppWorkDir = None

# The address (?) and port that the server will serve
ServerAddress = ('', 8080)

try:
	import os, sys, string
	if not WebwareDir:
		WebwareDir = os.path.dirname(os.path.dirname(os.getcwd()))
        sys.path.insert(0, WebwareDir)
	webKitDir = os.path.join(WebwareDir, 'WebKit')
	if AppWorkDir is None:
		AppWorkDir = webKitDir
	else:
		sys.path.insert(0, AppWorkDir)

	from WebKit.Adapters.Adapter import Adapter
        (host, port) = string.split(open(os.path.join(webKitDir, 'address.text')).read(), ':')
        if os.name=='nt' and host=='': # MS Windows doesn't like a blank host name
            host = 'localhost'
        port = int(port)
except 0:
    ## @@: Is there something we should do with exceptions here?
    ## I'm apt to just let them print to stderr and quit like normal,
    ## but I'm not sure.
    pass

from WebKit.Experimental.HTTPServer import HTTPHandler, run

class HTTPAdapter(HTTPHandler, Adapter):

    def __init__(self, *vars):
        Adapter.__init__(self, webKitDir)
        HTTPHandler.__init__(self, *vars)

    def doTransaction(self, env, myInput):
        self.transactWithAppServer(env, myInput, host, port)
        

if __name__ == '__main__':
    if len(sys.argv) > 1 and \
       sys.argv[1] == 'daemon':
        if os.fork() or os.fork():
            sys.exit(0)
    run(ServerAddress, HTTPAdapter)

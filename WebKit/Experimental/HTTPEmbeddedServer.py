from HTTPServer import HTTPHandler, ThreadedHTTPServer, HaltServer
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from WebKit.ASStreamOut import ASStreamOut
import threading, time

True, False = 1==1, 0==1

ServerAddress = ('', 8080)

class HTTPEmbeddedServer(HTTPHandler):

    def doTransaction(self, env, myInput):
        dict = {'format': 'CGI',
                'time': time.time(),
                'environ': env,
                'input': myInput,
                }
        streamOut = ASStreamOut()
        transaction = self._appServer.application().dispatchRawRequest(dict, streamOut)
        streamOut.close()
        transaction.die()
        self.processResponse(streamOut._buffer)

class PortServer:

    def __init__(self, serverAddress=ServerAddress):
        self._serverAddress = serverAddress

    def start(self, appServer):
        HTTPEmbeddedServer._appServer = appServer
        httpd = ThreadedHTTPServer(self._serverAddress, HTTPEmbeddedServer)
        t = threading.Thread(target=httpd.serve_forever)
        t.start()
        self._thread = t
        self._httpd = httpd

    def shutDown(self):
        self._httpd.shutDown()
        self._thread.join()



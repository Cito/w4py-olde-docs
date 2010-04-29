#!/usr/bin/env python

"""WSGIAdapter.py

This is the WSGI Adapter for the WebKit AppServer.

This script expects to find a file in its directory called
'adapter.address' that specifies the address of the app server.
If the address file is not found, the address is taken from
the configuration file called 'WSGIAdapter.conf'.

Contributed to Webware for Python by Christoph Zwerschke, 04/2010.

"""

# If you used the MakeAppWorkDir.py script to make a separate
# application working directory, specify it here:
workDir = None

# If the Webware installation is located somewhere else,
# then set the webwareDir variable to point to it here:
webwareDir = None

import os, sys

if not webwareDir:
    webwareDir = os.path.dirname(os.path.dirname(
        os.path.abspath(os.path.dirname(__file__))))
sys.path.insert(0, webwareDir)
webKitDir = os.path.join(webwareDir, 'WebKit')
sys.path.insert(0, webKitDir)
if not workDir:
    workDir = webKitDir

from WebKit.Adapters.Adapter import Adapter


class StdErr(object):
    """Auxiliary store for temporary redirection of sys.stderr."""
    def __init__(self, stderr):
        if stderr:
            self.stderr, sys.stderr = sys.stderr, stderr
        else:
            self.stderr = None
    def close(self):
        if self.stderr:
            self.stderr, sys.stderr = None, self.stderr
    def __del__(self):
        self.close()


class WSGIAdapter(Adapter):
    """WSGI application interfacing to the Webware application server."""

    def __call__(self, environ, start_response):
        """The actual WSGI application."""
        err = StdErr(environ.get('wsgi.errors', None))
        try:
            inp = environ.get('wsgi.input', None)
            if inp is not None:
                try:
                    inp_len = int(environ['CONTENT_LENGTH'])
                    if inp_len <= 0:
                        raise ValueError
                except (KeyError, ValueError):
                    inp = None
                else:
                    try:
                        inp = inp.read(inp_len)
                    except IOError:
                        inp = None
            # we pass only environment variables that can be marshalled
            environ = dict(item for item in environ.iteritems()
                if isinstance(item[1], (bool, int, long, float,
                    str, unicode, tuple, list, set, frozenset, dict)))
            response = self.getChunksFromAppServer(environ, inp or '')
            header = []
            for chunk in response:
                if header is None:
                    yield chunk
                else:
                    chunk = chunk.split('\r\n\r\n', 1)
                    header.append(chunk[0])
                    if len(chunk) > 1:
                        chunk = chunk[1]
                        header = ''.join(header).split('\r\n')
                        status = header.pop(0).split(': ', 1)[-1]
                        header = [tuple(line.split(': ', 1)) for line in header]
                        start_response(status, header)
                        header = None
                        if chunk:
                            yield chunk
        except:
            # This is a workaround for Python 2.4 which does not allow a
            # yield statement to live in a try block with a finally clause.
            # Note that this also works if the generator is simply abandoned
            # even though Python 2.4 does not raise a GeneratorExit, because
            # if the generator is deleted, the local variable err also gets
            # deleted and its close() method will be called by its destructor.
            err.close()
        else:
            err.close()


# Create one WSGI application instance:

wsgiAdapter = WSGIAdapter(workDir)

application = wsgiAdapter # the name expected by mod_wsgi

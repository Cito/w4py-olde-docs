#!/usr/bin/env python

"""WSGIAdapter.py

This is the WSGI Adapter for the WebKit AppServer.

This script expects to find a file in its directory called
'adapter.address' that specifies the address of the app server.
If the address file is not found, the address is taken from
the configuration file called 'WSGIAdapter.conf'.

Contributed to Webware for Python by Christoph Zwerschke, 04/2010.

"""

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

from WebKit.Adapters.Adapter import Adapter


class WSGIAdapter(Adapter):
    """WSGI application interfacing to the Webware application server."""

    def __init__(self, webKitDir=webKitDir):
        """Create a new WSGI Adapter in the given WebKit directory."""
        Adapter.__init__(self, webKitDir)
        try:
            host, port = open(os.path.join(self._webKitDir,
                'adapter.address')).read().split(':', 1)
        except Exception:
            host = port = None
        else:
            if os.name == 'nt' and not host:
                host = 'localhost' # MS Windows doesn't like a blank host name
            try:
                port = int(port)
            except ValueError:
                port = None
        self._host, self._port = host, port

    def __call__(self, environ, start_response):
        """The actual WSGI application."""
        errors = environ.get('wsgi.errors', None)
        if errors is not None:
            errors, sys.stderr = sys.stderr, errors
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
            response = self.getChunksFromAppServer(
                environ, inp or '', self._host, self._port)
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
        finally:
            if errors is not None:
                sys.stderr = errors


# Create one WSGI application instance:

wsgiAdapter = WSGIAdapter()

application = wsgiAdapter # the name expected by mod_wsgi

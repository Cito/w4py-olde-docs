#!/usr/bin/env python

"""CGIPlusAppServer

This WebKit app server is a WASD CGIplus server that accepts requests, hands
them off to the Application and sends the request back over the connection.

The fact that the app server stays resident is what makes it so much quicker
than traditional CGI programming. Everything gets cached.

CGIPlusAppServer takes the following command line arguments:

start: start the AppServer (default argument)
stop: stop the currently running Apperver
ClassName.SettingName=value: change configuration settings

When started, the app server records its pid in appserver.pid.

"""

import os
import sys
import traceback

from time import time

from MiscUtils import StringIO
from MiscUtils.Funcs import asclocaltime

import AppServer as AppServerModule
from AutoReloadingAppServer import AutoReloadingAppServer as AppServer


debug = False

server = None


class CgiPlusAppServer(AppServer):

    ## Init ##

    def __init__(self, path=None):
        AppServer.__init__(self, path)
        self._requestID = 1
        self.recordPID()
        self._wasd_running = None

        # temporaire
        from WebKit import Profiler
        Profiler.startTime = time()
        self.readyForRequests()

    def addInputHandler(self, handlerClass):
        self._handler = handlerClass

    def isPersistent(self):
        return False

    def recordPID(self):
        """Currently do nothing."""
        return

    def initiateShutdown(self):
        self._wasd_running = False
        AppServer.initiateShutdown(self)

    def mainloop(self, timeout=1):
        import wasd
        wasd.init()
        stderr_ini = sys.stderr
        sys.stderr = StringIO()
        self._wasd_running = True
        environ_ini = os.environ
        while 1:
            if not self._running or not self._wasd_running:
                return
            # init environment cgi variables
            os.environ = environ_ini.copy()
            wasd.init_environ()
            print >> sys.__stdout__, "Script-Control: X-stream-mode"
            self._requestID += 1
            self._app._sessions.cleanStaleSessions()
            self.handler = handler = self._handler(self)
            handler.activate(self._requestID)
            handler.handleRequest()
            self.restartIfNecessary()
            self.handler = None
            sys.__stdout__.flush()
            if not self._running or not self._wasd_running:
                return
            # when we want to exit don't send the eof, so
            # WASD don't try to send the next request to the server
            wasd.cgi_eof()
            sys.stderr.close()
            # block until next request
            wasd.cgi_info("")
            sys.stderr = StringIO()

    def shutDown(self):
        self._running = 0
        print "CgiPlusAppServer: Shutting Down"
        AppServer.shutDown(self)


class Handler:

    def __init__(self, server):
        self._server = server

    def activate(self, requestID):
        """Activates the handler for processing the request.

        Number is the number of the request, mostly used to identify
        verbose output. Each request should be given a unique,
        incremental number.

        """
        self._requestID = requestID

    def close(self):
        pass

    def handleRequest(self):
        pass

    def receiveDict(self):
        """Utility function to receive a marshalled dictionary."""
        pass


from WebKit.ASStreamOut import ASStreamOut
class CPASStreamOut(ASStreamOut):
    """Response stream for CgiPLusAppServer.

    The `CPASASStreamOut` class streams to a given file, so that when `flush`
    is called and the buffer is ready to be written, it sends the data from the
    buffer out on the file. This is the response stream used for requests
    generated by CgiPlusAppServer.

    CP stands for CgiPlusAppServer

    """

    def __init__(self, file):
        ASStreamOut.__init__(self)
        self._file = file

    def flush(self):
        result = ASStreamOut.flush(self)
        if result: # a true return value means we can send
            reslen = len(self._buffer)
            self._file.write(self._buffer)
            self._file.flush()
            sent = reslen
            self.pop(sent)


# Set to False in DebugAppServer so Python debuggers can trap exceptions
doesRunHandleExceptions = True

class RestartAppServerError(Exception):
    """Raised by DebugAppServer when needed."""
    pass


def run(workDir=None):
    global server
    from WebKit.CgiPlusServer import CgiPlusAppServerHandler
    runAgain = True
    while runAgain: # looping in support of RestartAppServerError
        try:
            try:
                runAgain = False
                server = None
                server = CgiPlusAppServer(workDir)
                server.addInputHandler(CgiPlusAppServerHandler)
                try:
                    server.mainloop()
                except KeyboardInterrupt, e:
                    server.shutDown()
            except RestartAppServerError:
                print
                print "Restarting app server:"
                sys.stdout.flush()
                runAgain = True
            except Exception, e:
                if not doesRunHandleExceptions:
                    raise
                if not isinstance(e, SystemExit):
                    traceback.print_exc(file=sys.stderr)
                print
                print "Exiting AppServer"
                if server:
                    if server._running:
                        server.initiateShutdown()
                # if we're here as a result of exit() being called,
                # exit with that return code.
                if isinstance(e, SystemExit):
                    sys.exit(e)
        finally:
            AppServerModule.globalAppServer = None
    sys.exit()


# Signal handlers

def shutDown(arg1, arg2):
    print "Shutdown Called", asclocaltime()
    if server:
        server.initiateShutdown()
    else:
        print 'WARNING: No server reference to shutdown.'

import signal
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)


# Command line interface

import re
usage = re.search('\n.* arguments:\n\n(.*\n)*?\n', __doc__).group(0)
settingRE = re.compile(r'^--([a-zA-Z][a-zA-Z0-9]*\.[a-zA-Z][a-zA-Z0-9]*)=')
from MiscUtils import Configurable

def main(args):
    function = run
    workDir = None
    sys.stdout = StringIO()
    for arg in args[:]:
        if settingRE.match(arg):
            match = settingRE.match(arg)
            name = match.group(1)
            value = arg[match.end():]
            Configurable.addCommandLineSetting(name, value)
        elif arg == "stop":
            function = AppServerModule.stop
        elif arg == "start":
            pass
        elif arg[:8] == "workdir=":
            workDir = arg[8:]
        else:
            print usage

    function(workDir=workDir)

main([])

#!/usr/bin/env python
"""
Version of AppServer that uses threads and the asyncore module.
"""


from AppServer import AppServer
from Application import Application
from marshal import dumps, loads
import os, sys
from threading import Lock, Thread
import Queue
import select
import socket
import asyncore


class AsyncThreadedAppServer(asyncore.dispatcher, AppServer):
    """

    """

    ## Init ##

    def __init__(self):

        AppServer.__init__(self)

        self._addr = None
        self._poolsize=self.setting('ServerThreads')

        self.threadPool=[]
        self.requestQueue=Queue.Queue(self._poolsize*5) #5 times the number of threads we have
        self.rhQueue=Queue.Queue(0)#must be larger than requestQueue, just make it no limit, and limit the number that can be created
        self._maxRHCount = self._poolsize * 10
        self.rhCreateCount = 0

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = self.address()
        self.bind(addr)
        print "Listening on", addr
        open('address.text', 'w').write('%s:%d' % (addr[0], addr[1]))

        self.running=1

        out = sys.stdout
        out.write('Creating %d threads' % self._poolsize)
        for i in range(self._poolsize): #change to threadcount
            t = Thread(target=self.threadloop)
            t.start()
            self.threadPool.append(t)
            out.write(".")
            out.flush()
        out.write("\n")

        #self.asyn_thread = Thread(target=self.asynloop)
        #self.asyn_thread.start()

        self.listen(1024) # @@ 2000-07-14 ce: hard coded constant should be a setting
        print "Ready\n"


    def handle_accept(self):
        """
        This is the function that starts the request processing cycle.  When asyncore senses a write on the main socket, it calls this function.  We then accept the connection, and hand it off to a RequestHandler instance by calling the RequestHandler instance's activate method.  When we call that activate method, the RH registers itself with asyncore by calling set_socket, so that asyncore now will include that socket, and thus the RH, in it's network select loop.
        """
        #print "Accepting"
        conn,addr = self.accept()
        conn.setblocking(0)
        self._reqCount = self._reqCount+1
        rh = None
        try:
            rh=self.rhQueue.get_nowait()
        except Queue.Empty:
            if self.rhCreateCount < self._maxRHCount:
                rh = RequestHandler(self)
                self.rhCreateCount = self.rhCreateCount + 1
            else:
                rh = self.rhQueue.get() #block
        rh.activate(conn)

    def readable(self):
        return self.accepting

    def writable(self):
        return 0

    def handle_connect(self):
        pass

    def log(self, message):
       pass

    def asynloop(self):
        """
        Not used currently
        """
        while self.running:
            #print "asyncore loop"
            asyncore.loop()

    def address(self):
        if self._addr is None:
            self._addr = (self.setting('Host'), self.setting('Port'))
        return self._addr




    def threadloop(self):
        """
        Try to get a RequestHandler instance off the requestQueue and process it.
        """
        while self.running:
            try:
                rh=self.requestQueue.get()
                if rh == None: #None means time to quit
                    break
                rh.handleRequest()      #this is all there is to it
            except Queue.Empty:
                pass


    def shutDown(self):
        """
        Cleanup when being shut down.
        """
        self._app.shutDown()
        #self.mainsocket.close()
        for i in range(self._poolsize):
            self.requestQueue.put(None)#kill all threads
        for i in self.threadPool:
            i.join()
        del self._plugIns[:]

        del self._app



import string, time

class RequestHandler(asyncore.dispatcher):
    """
    Has the methods that process the request.
    An instance of this class is activated by AppServer.  When activated, it is listening for the request to come in.  asyncore will call handle_read when there is data to be read.  ONce all the request has been read, it will put itself in the requestQueue to be picked up by a thread and processed by calling handleRequest. Once the processing is complete, the thread drops the instance and tries to find another one.  This instance notifies asyncore that it is ready to send.
    """


    def __init__(self, server):
        self.server=server
        self.have_request = 0
        self.have_response = 0
        self.reqdata=[]
        self._buffer = ''

    def handleRequest(self):

        verbose = self.server._verbose

        startTime = time.time()
        if verbose:
            print 'BEGIN REQUEST'
            print time.asctime(time.localtime(startTime))

        if verbose:
            print 'receiving request from', self.socket

        while not self.have_request:
            print ">> Should always have request before we get here"
            time.sleep(0.01)

        if verbose:
            print 'received %d bytes' % len(self.reqdata)
        if self.reqdata:
            dict = loads(self.reqdata)
            if verbose:
                print 'request has keys:', string.join(dict.keys(), ', ')
                if dict.has_key('environ'):
                    requestURI = dict['environ'].get('REQUEST_URI', None)
                else:
                    requestURI = None
                print 'request uri =', requestURI


        transaction = self.server._app.dispatchRawRequest(dict)
        rawResponse = dumps(transaction.response().rawResponse())

        self._buffer = rawResponse
        self.have_response = 1

        if verbose:
            print 'connection closed.'
            print '%0.2f secs' % (time.time() - startTime)
            print 'END REQUEST'
            print

        transaction._application=None
        transaction.die()
        del transaction

    def activate(self, socket):
        self.set_socket(socket)
        self._buffer=''
        self.active = 1

    def readable(self):
        return self.active and not self.have_request

    def writable(self):
        """
        Always ready to write, otherwise we might have to wait for a timeout to be asked again
        """
        return self.active
        #return self.have_response

    def handle_connect(self):
        pass

    def handle_read(self):
        data = self.recv(8192)
        if len(data) == 8192:
            self.reqdata.append(data)
        else:
            self.reqdata.append(data)
            self.reqdata = string.join(self.reqdata,'')
            self.have_request=1
            self.server.requestQueue.put(self)
            #self.socket.shutdown(0)

    def handle_write(self):
        if not self.have_response: return
        sent = self.send(self._buffer)
        self._buffer = self._buffer[sent:]
        if len(self._buffer) == 0:
            self.close()
            #For testing
            #sys.stdout.write(".")
            #sys.stdout.flush()

    def close(self):
        self.active = 0
        self.have_request = 0
        self.have_response = 0
        self.reqdata=[]
        asyncore.dispatcher.close(self)
        self.server.rhQueue.put(self)

    def log(self, message):
        pass



def main():
    try:
        server = AsyncThreadedAppServer()
        asyncore.loop()
    except Exception, e: #Need to kill the Sweeper thread somehow
        print e
        print "Exiting AppServer"
        server.running=0
        server.shutDown()
        del server
        sys.exit()


if __name__=='__main__':
    main()

#!/usr/bin/env python
'''
stress.py
By Chuck Esterbrook
Mods by Jay Love

Purpose: Hit the WebKit AppServer with lots of a requests in order to:
	* Test for memory leaks
	* Test concurrency
	* Investigate performance

This stress test skips the web server and the WebKit adaptor, so it's not
useful for measuring absolute performance. However, after making a
modification to WebKit or your web-based application, it can be useful to
see the relative difference in performance (although still somewhat
unrealistic).

To Run:
	> stress.py  -OR-
	> python stress.py

This will give you the usage (and examples) which is:
	stress.py numRequests [minParallelRequests [maxParallelRequests [delay]]]

Programmatically, you could could also import this file and use the
stress() function.

To capture additional '.rr' files, which contain raw request
dictionaries, make use of the CGIAdaptor and uncomment the lines therein
that save the raw requests.
'''


import sys, string, os, time
from glob import glob
from socket import *
from marshal import dumps
from thread import start_new_thread
from whrandom import randint
from time import asctime, localtime, time, sleep
from threading import Thread


def usage():
	''' Prints usage of this program and exits. '''
	sys.stdout = sys.stderr
	name = sys.argv[0]
	print '%s usage:' % name
	print '  %s numRequests [minParallelRequests [maxParallelRequests [delay]]]' % name
	print 'Examples:'
	print '  %s 100            # run 100 sequential requests' % name
	print '  %s 100 5          # run 100 requests, 5 at a time' % name
	print '  %s 100 5 10       # run 100 requests, 5-10 at a time' % name
	print '  %s 100 10 10 0.01 # run 100 requests, 10 at a time, with a delay between each set' % name
	print
	sys.exit(1)


def request(name, dict, host, port, bufsize):
	''' Performs a single AppServer request including sending the request and receiving the response. '''

	# Update the time stamp to now
	dict['time'] = time()

	# Taken from CGIAdaptor:
	s = socket(AF_INET, SOCK_STREAM)
	s.connect(host, port)
	s.send(dumps(dict))
	s.shutdown(1)
	while 1:
		data = s.recv(bufsize)
		if not data:
			break
		#sys.stdout.write(data)
	# END


def stress(maxRequests, minParallelRequests=1, maxParallelRequests=1, delay=0.0):
	''' Executes a stress test on the AppServer according to the arguments. '''

	# Taken from CGIAdaptor:
	(host, port) = string.split(open('../address.text').read(), ':')
	if os.name=='nt' and host=='': # MS Windows doesn't like a blank host name
		host = 'localhost'
	port = int(port)
	bufsize = 32*1024
	# END

	# Get the requests from .rr files which are expected to contain raw request dictionaries
	requestFilenames = glob('*.rr')
	requestDicts = map(lambda filename: eval(open(filename).read()), requestFilenames)
	requestCount = len(requestFilenames)
	count = 0

	if maxParallelRequests<minParallelRequests:
		maxParallelRequests = minParallelRequests
	sequential = minParallelRequests==1 and maxParallelRequests==1

	startTime = time()
	count = 0
	print 'STRESS TEST for Webware.WebKit.AppServer'
	print
	print 'time                =', asctime(localtime(time()))
	print 'requestFilenames    =', requestFilenames
	print 'maxRequests         =', maxRequests
	print 'minParallelRequests =', minParallelRequests
	print 'maxParallelRequests =', maxParallelRequests
	print 'delay               = %0.02f' % delay
	print 'sequential          =', sequential
	print 'Running...'
	while count<maxRequests:
		if sequential:
			i = randint(0, requestCount-1)
			filename = requestFilenames[i]
			dict = requestDicts[i]
			request(filename, dict, host, port, bufsize)
			count = count + 1
		else:
			threads = []
			numRequests = randint(minParallelRequests, maxParallelRequests)
			for i in range(numRequests):
				i = randint(0, requestCount-1)
				filename = requestFilenames[i]
				dict = requestDicts[i]
				thread = Thread(target=request, args=(filename, dict, host, port, bufsize))
				thread.start()
				threads.append(thread)
				count = count + 1
				if count==maxRequests:
					break
			# Wait til all threads are finished
			for thread in threads:
				thread.join()
			threads = None
		if delay:
			sleep(delay)
	duration = time()-startTime
	print 'count                = %d' % count
	print 'duration             = %0.2f' % duration
	print 'secs/page            = %0.2f' % (duration/count)
	print 'pages/sec            = %0.2f' % (count/duration)
	print 'Done.'
	print


if __name__=='__main__':
	if len(sys.argv)==1:
		usage()
	else:
		args = map(lambda arg: eval(arg), sys.argv[1:])
		apply(stress, args)

#!/usr/bin/env python

"""
Fault tolerance system for WebKit

author: Jay Love

This module is intended to provide additional assurance that the AppServer continues running
at all times.  This module will be reponsible for starting the AppServer, and monitoring its
health.  It does that by periodically sending a status check message to the AppServer to ensure
that it is responding.  If it finds that the AppServer does not respond within a specified time,
it will start a new copy of the AppServer, after killing the previous process.
*******************************************************************************************
USE:


"Monitor start"
 or
"Monitor stop"


The default specified below will be used, or you can list the AppServer you would like after "start".

You can have the whole process run as a daemon by specifying "daemon" after "start" on the command line.

To stop the processes, run "Monitor.py stop".

********************************************************************************************
Future:
Add ability to limit number of requests served.  When some count is reached, send
a message to the server to save it's sessions, then exit.  Then start a new AppServer
that will pick up those sessions.

It should be possible on both Unix and Windows to monitor the AppServer process in 2 ways:
1) The method used here, ie can it service requests?
2) is the process still running?

Combining these with a timer lends itself to load balancing of some kind.


"""



defaultServer = "AsyncThreadedAppServer"



import socket
import time
import os
import asyncore
import sys
import signal
import string

global serverName
serverName = defaultServer
global srvpid
srvpid=0
checkInterval = 10  #add to config if this implementation is adopted, seconds between checks
maxStartTime = 120  #time to wait for a AppServer to start before killing it and trying again
global addr
global running
running = 0

debug = 0


def createServer(changeDirectory=0):
	"""Unix only, after forking"""
	print "Starting Server"
	if changeDirectory:
		os.chdir(os.pardir)
		if '' not in sys.path:
			sys.path = [''] + sys.path
	import WebKit
	code = 'from WebKit.%s import main' % serverName
	exec code
	main(['monitor',])


def startupCheck():
	"""
	Make sure the AppServer starts up correctly.
	"""
	global debug
	count = 0
	while 1: #give the server a chance to start
		if checkServer(0):
			break
		print "Waiting for start"
		time.sleep(checkInterval)
		count = count + checkInterval
		if count > maxStartTime:
			print "Couldn't start AppServer"
			print "Killing AppServer"
			os.kill(srvpid,signal.SIGKILL)
			sys.exit(1)


def startServer(killcurrent = 1):
	"""
	Start the AppServer.
	"""
	global srvpid
	global debug
	if os.name == 'posix':
		if killcurrent:
			os.kill(srvpid,signal.SIGTERM)
			os.waitpid(srvpid,0) #prevent zombies
		srvpid = os.fork()
		if srvpid == 0:
			createServer(not killcurrent)
			sys.exit()
	
	

def checkServer(restart = 1):
	"""
	Send a check request to the AppServer.  If restart is 1, then
	attempt to restart the server if we can't connect to it.

	This function could also be used to see how busy an AppServer is by measuring the delay in
	getting a response when using the standard port.
	"""
	global addr
	global running
	try:
		sts = time.time()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(addr)
		s.send("STATUS")
		s.shutdown(1)
		resp = s.recv(9)  #up to 1 billion requests!
		monwait = time.time() - sts
		if debug:
			print "Processed %s Requests" % resp
			print "Delay %s" % monwait
		return 1
	except:
		print "No Response from AppServer"
		if running and restart:
			startServer()
			startupCheck()
		else:
			return 0
		


def main(args):
	global debug
	global serverName
	global running

	running = 1
	
	file = open("monitorpid.txt","w")
	if os.name == 'posix':
		file.write(str(os.getpid()))
	file.flush()
	file.close()
	startServer(0)
	try:
		startupCheck()
		while running:
			try: 
				checkServer()
				if debug:
					print "Checking Server"
				time.sleep(checkInterval)
			except Exception, e:
				if debug:
					print "Exception %s" % e
				print "Exiting Monitor"
				os.kill(srvpid,signal.SIGTERM)
				sys.exit()
	except Exception, e:
		if debug:
			print "Exception %s" % e
			print "Exiting Monitor"
		os.kill(srvpid,signal.SIGTERM)
		sys.exit()		


def shutDown(arg1,arg2):
	global running
	print "Monitor Shutdown Called"
	running = 0
	global addr
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(addr)
		s.send("QUIT")
		s.shutdown(1)
		resp = s.recv(10)
		s.close()
		print "Server response to shutdown request:", resp
	except Exception, e:
		print "No Response to Shutdown Request, performing hard kill"
		os.kill(srvpid, signal.SIGTERM)
		os.waitpid(srvpid,0)

import signal
signal.signal(signal.SIGINT, shutDown)
signal.signal(signal.SIGTERM, shutDown)


def stop():
		pid = int(open("monitorpid.txt","r").read())
		os.kill(pid,signal.SIGINT)    #this goes to the other running instance of this module


def usage():
	print """
This module serves as a watcher for the AppServer process.
The required command line argument is one of:
start: Starts the monitor and default appserver
stop:  Stops the currently running Monitor process and the AppServer it is running.  This is the only way to stop the process other than hunting down the individual process ID's and killing them.


Optional arguments:
"AppServerClass":  The AppServer class to use (AsyncThreadedAppServer or ThreadedAppServer)
daemon:  If "daemon" is specified, the Monitor will run in the background.\n
Stopping:
	
"""

arguments = ["start", "stop"]
servernames = ["AsyncThreadedAppServer", "ThreadedAppServer"]
optionalargs = ["daemon"]


if __name__=='__main__':
	global addr

	if os.name != 'posix':
		print "This service can only be run on posix machines (UNIX)"
		sys.exit()
		
	if len(sys.argv) == 1:
		usage()
		sys.exit()

	args = sys.argv[1:]
	if args[0] not in arguments:
		usage()
		sys.exit()

	cfg = open("Configs/AppServer.config")
	cfg = eval(cfg.read())
	addr = ((cfg['Host'],cfg['Port']-1))


	if 'stop' in args:
		stop()
		sys.exit()

	for i in servernames:
		if i in args:
			serverName=i
			
		
	if 'daemon' in args: #fork and become a daemon
		daemon=os.fork()
		if daemon:
			sys.exit()


	main(args)












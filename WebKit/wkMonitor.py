#!/usr/bin/env python

"""
Quick and dirty fault tolerance system for WebKit

author: Jay Love

(Or maybe I don't want to put my name on this one? ;0 )


Future:
Add ability to limit number of requests served.  When some count is reached, send
a message to the server to save it's sessions, then exit.  Then start a new AppServer
that will pick up those sessions.

It should be possible on both Unix and Windows to monitor the AppServer process in 2 ways:
1) The method used here, ie can it service requests?
2) is the process still running?

Combining these with a timer lends itself to load balancing of some kind.


"""

#These need to be filled in correctly on Windows
pythonexec = "C:\progra~1\python\python"
appserver = "e:\Linux\python\webware\webkit\AsyncThreadedAppServer.py"


import AppServer
import socket
import time
import AsyncThreadedAppServer
import os
import asyncore
import sys
import signal
import string


#Windows Specific Section
if os.name == 'nt':
	import win32process


srvpid = 0
checkInterval = 10  #add to config if this implementation is adopted, seconds between checks
maxStartTime = 120  #time to wait for a AppServer to start before killing it and trying again

cfg = open("Configs/AppServer.config")
cfg = eval(cfg.read())
addr = ((cfg['Host'],cfg['Port']-1))

debug = 0


def createServer():
	"""Unix only, after forking"""
	print "Starting Server"
	AsyncThreadedAppServer.main(1)


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
		time.sleep(interval)
		count = count + interval
		if count > maxStartTime:
			print "Couldn't start AppServer"
			if os.name == 'posix':
				print "Killing AppServer"
				os.kill(srvpid,signal.SIGKILL)
			else:
				win32process.TerminateProcess(srvpid,0)
			sys.exit(1)


def startServer(killcurrent = 1):
	"""
	Start the AppServer.
	"""
	global srvpid
	global debug
	if os.name == 'posix':
		if killcurrent:
			os.kill(srvpid,signal.SIGQUIT)
			os.waitpid(srvpid,0) #prevent zombies
		srvpid = os.fork()
		if srvpid == 0:
			createServer()
			sys.exit()
	elif os.name == 'nt':
		if killcurrent:
			win32process.TerminateProcess(srvpid,0)
		print "Starting %s" % appserver
		srvpid = os.spawnve(os.P_NOWAIT, pythonexec, [pythonexec,appserver,"-monitor"],os.environ)
	else:
		print "I don't recognize your OS!\nSorry, but I must quit.\n You can run the AppServer by itself, though!"
		sys.exit(0)
	
	

def checkServer(restart = 1):
	"""
	Send a check request to the AppServer.  If restart is 1, then
	attempt to restart the server if we can't connect to it.

	This function could also be used to see how busy an AppServer is by measuring the delay in
	getting a response when using the standard port.
	"""
	global debug
	try:
		sts = time.time()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(addr)
		s.send("STATUS")
		s.shutdown(1)
		resp = s.recv(9)#up to 1 billion requests!
		monwait = time.time() - sts
		if debug:
			print "Processed %s Requests" % resp
			print "Delay %s" % monwait
		return 1
	except:
		if restart:
			startServer()
			startupCheck()
		else:
			return 0
		


def main():
	global debug
	startServer(0)
	startupCheck()
	
	while 1:
		try: 
			time.sleep(interval)
			checkServer()
			if debug:
				print "Checking Server"
		except:
			print "Exiting Monitor"
			if os.name == 'posix':
				print "Killing AppServer"
				os.kill(srvpid,signal.SIGQUIT)
			else:
				print "Killing AppServer"
				win32process.TerminateProcess(srvpid,0)
			sys.exit()
		



if __name__=='__main__':
    main()












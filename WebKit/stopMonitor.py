#!/usr/bin/env python
import socket
import time
import os
import sys
import signal
import string


#Windows Specific Section
if os.name == 'nt':
	import win32process


pid = int(open("monitorpid.txt","r").read())


if os.name == "posix":
	os.kill(pid,signal.SIGINT)
else:
	##this isn't working
	win32process.TerminateProcess(pid,0)



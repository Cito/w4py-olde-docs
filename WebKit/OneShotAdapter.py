'''
OneShotAdapter.py

This is a special version of the CGIAdapter that doesn't require a persistent AppServer process. This is mostly useful during development when repeated changes to classes forces the developer to restart the app server to make the changes take effect.

An example, URL:

	http://127.0.0.1/OneShot.cgi/MyPage

'''


# 2000-08-07 ce: For accuracy purposes, we want to record the timestamp as early as possible.
import time
_timestamp = time.time()


# 2000-08-07 ce: We have to reassign sys.stdout *immediately* because it's referred to as a default parameter value in Configurable.py which happens to be our ancestor class as well as the ancestor class of AppServer and Application. The Configurable method that uses sys.stdout for a default parameter value must not execute before we rewire sys.stdout. Tricky, tricky.
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO
import sys
_real_stdout = sys.stdout
sys.stdout = _console = StringIO()  # to capture the console output of the application



import os, string

from Adapter import *


class OneShotAdapter(Adapter):

	def defaultConfig(self):
		config = Adapter.defaultConfig(self)
		config.update({
			'ShowConsole':           0,
			'ConsoleWidth':          80,  # use 0 to turn off
			'ConsoleHangingIndent':  4,
		})
		return config

	def run(self):

		try:
			myInput = sys.stdin.read()

			dict = {
				'format':  'CGI',
				'time':    _timestamp,
				'environ': os.environ.data, # ce: a little tricky. We use marshal which only works on built-in types, so we need environ's dictionary
				'input':   myInput
			}

			print 'ONE SHOT MODE\n'

			from OneShotAppServer import OneShotAppServer
			appSvr = OneShotAppServer()
			response = appSvr.dispatchRawRequest(dict).response().rawResponse()
			appSvr.shutDown()
			appSvr = None

			sys.stdout = _real_stdout
			if os.name=='nt': # MS Windows: no special translation of end-of-lines
				import msvcrt
				msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
			write = sys.stdout.write
			for pair in response['headers']:
				write('%s: %s\n' % pair)
			write('\n')
			write(response['contents'])
			if self.setting('ShowConsole'):
				self.showConsole(_console.getvalue())
		except:
			import traceback

			sys.stderr.write('[%s] [error] WebKitCGIAdaptor: Error while responding to request (unknown)\n' % (time.asctime(time.localtime(time.time()))))
			sys.stderr.write('Python exception:\n')
			traceback.print_exc(file=sys.stderr)

			output = apply(traceback.format_exception, sys.exc_info())
			output = string.join(output, '')
			output = string.replace(output, '&', '&amp;')
			output = string.replace(output, '<', '&lt;')
			output = string.replace(output, '>', '&gt;')
			output = string.replace(output, '"', '&quot;')
			sys.stdout.write('''Content-type: text/html

<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)

	def showConsole(self, contents):
		width = self.setting('ConsoleWidth')
		if width:
			contents = WordWrap(contents, self.setting('ConsoleWidth'), self.setting('ConsoleHangingIndent'))
		contents = HTMLEncode(contents)
		sys.stdout.write('<br><p><table><tr><td bgcolor=#EEEEEE><pre>%s</pre></td></tr></table>' % contents)


def main():
	try:
		OneShotAdapter().run()
	except:
		import traceback

		sys.stderr.write('[%s] [error] OneShotAdapter: Error while responding to request (unknown)\n' % (time.asctime(time.localtime(time.time()))))
		sys.stderr.write('Python exception:\n')
		traceback.print_exc(file=sys.stderr)

		output = apply(traceback.format_exception, sys.exc_info())
		output = string.join(output, '')
		output = string.replace(output, '&', '&amp;')
		output = string.replace(output, '<', '&lt;')
		output = string.replace(output, '>', '&gt;')
		output = string.replace(output, '"', '&quot;')
		sys.stdout.write('''Content-type: text/html

<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)


if __name__=='__main__':
	main()

import os
from time import time, localtime, sleep

from WebUtils.Funcs import requestURI
from AdminSecurity import AdminSecurity

def strtime(t):
	return '%4d-%02d-%02d %02d:%02d:%02d' % localtime(t)[:6]


class ThreadControl(AdminSecurity):

	def title(self):
		return 'ThreadControl'

	def writeContent(self):
		app = self.application()
		server = app.server()
		request = self.request()
		field = request.field
		myRequestID = request.requestID()
		wr = self.writeln

		abortRequest = getattr(server, 'abortRequest', None)
		threadPool = getattr(server, '_threadPool', [])

		try:
			max_duration = int(field('duration'))
		except (KeyError, ValueError):
			max_duration = 30

		wr('<h2>Current thread status</h2>')
		if abortRequest:
			wr('''<form action="ThreadControl" method="post">
<p><input name="cancel_all" type="submit" value="Cancel all requests below">
<input name="cancel_selected" type="submit" value="Cancel all selected requests">
<input name="refresh_view" type="submit" value="Refresh view"></p>
<p><input name="cancel_long" type="submit" value="Cancel all long-running requests">
(longer than <input type="text" name="duration" value="%d"
size="6" maxlength="12" style="text-align: right"> seconds)</p>
<p>You can <a href="Sleep" target="_blank">create a long-running request</a>
in a separate browser window for testing.</p>
<p>(Your web browser may get stuck if you create more than one of these.)</p>
''' % max_duration)
		else:
			wr('<p>(You need Python 2.3 with <code>ctypes</code>'
				' or a newer Python version to enable cancellation of threads.)</p>')

		if field('cancel_selected', None):
			killIDs = field('selectedIDs', None) or []
		elif field('cancel_all', None):
			killIDs = field('allIDs', '').split(',')
		elif field('cancel_long', None):
			killIDs = field('longIDs', None) or []
		else:
			killIDs = []
		if type(killIDs) != type([]):
			killIDs = [killIDs]
		try:
			killIDs = map(int, killIDs)
		except ValueError:
			killIDs = []
		killedIDs = []
		errorIDs = []
		activeThreads = []
		for thread in threadPool:
			try:
				handler = thread._processing
				if handler:
					activeThreads.append(handler._requestID)
			except Exception:
				continue
		for requestID in killIDs:
			if (not requestID or requestID == myRequestID
					or requestID not in activeThreads):
				continue
			if abortRequest:
				try:
					killed = abortRequest(requestID) == 1
				except Exception:
					killed = 0
			else:
				killed = 0
			if killed:
				killedIDs.append(requestID)
			else:
				errorIDs.append(requestID)
		if killedIDs:
			msg = (len(killedIDs) > 1 and
				'The following requests have been cancelled: %s'
					% ', '.join(map(str, killedIDs)) or
				'Request %d has been cancelled.' % killedIDs[0])
			wr('<p style="color:green">%s</p>' % msg)
			tries = 100
			while tries:
				pendingIDs = []
				for thread in threadPool:
					try:
						handler = thread._processing
						if handler:
							requestID = handler._requestID
							if requestID in killedIDs:
								pendingIDs.append(requestID)
					except Exception:
						continue
				if pendingIDs:
					sleep(0.125)
					tries -= 1
				else:
					pendingIDs = []
					tries = 0
			if pendingIDs:
				msg = (len(pendingIDs) > 1 and
					'The following of these are still pending: %s'
						% ', '.join(map(str, pendingIDs)) or
					'The request is still pending.')
				wr('<p>%s</p><p>You can'
					' <a href="ThreadControl">refresh the view<a>'
					' to verify cancellation.</p>' % msg)
		if errorIDs:
			msg = (len(errorIDs) > 1 and
				'The following requests could not be cancelled: %s'
					% ', '.join(map(str, errorIDs)) or
				'Request %d could not be cancelled.' % errorIDs[0])
			wr('<p style="color:red">%s</p>' % msg)

		threadCount = getattr(server, '_threadCount', 0)

		curTime = time()
		activeThreads = []
		for thread in threadPool:
			try:
				handler = thread._processing
				if handler:
					name = thread.getName()
					requestID = handler._requestID
					requestDict = handler._requestDict
					if requestID != requestDict['requestID']:
						raise ValueError
					startTime = requestDict.get('time')
					env = requestDict.get('environ')
					client = env and (env.get('REMOTE_NAME')
						or env.get('REMOTE_ADDR')) or None
					uri = env and requestURI(env) or None
					activeThreads.append((name, requestID,
						startTime, curTime - startTime, client, uri))
			except Exception:
				continue

		if activeThreads:
			headings = ('Thread name', 'Request ID', 'Start time',
				'Duration', 'Client', 'Request URI')
			sort = field('sort', None)
			wr('<table class="NiceTable"><tr>')
			column = 0
			sort_column = 1
			sort = field('sort', None)
			for heading in headings:
				sort_key = heading.lower().replace(' ', '_')
				if sort_key == sort:
					sort_column = column
				wr('<th><a href="ThreadControl?sort=%s">%s</a></th>'
					% (sort_key, heading))
				column += 1
			wr('<th>Cancel</th></tr>')
			def sort_threads(t1, t2, i=sort_column):
				v1, v2 = t1[i], t2[i]
				if v1 == v2:
					v1, v2 = t1[1], t2[1]
				elif i == 0:
					try:
						return cmp(int(v1.split('-')[-1]),
							int(v2.split('-')[-1]))
					except Exception:
						pass
				return cmp(v1, v2)
			activeThreads.sort(sort_threads)
		else:
			wr('<p>Could not determine the active threads.</p>')
		longIDs = []
		for (name, requestID, startTime, duration,
				client, uri) in activeThreads:
			if startTime:
				startTime = strtime(startTime)
				duration = int(duration + 0.5)
				if duration > 0:
					if duration > max_duration:
						duration = '<b>%s</b>' % duration
						if requestID:
							longIDs.append(requestID)
					duration = '%s&nbsp;s' % duration
				else:
					duration = int(1000*(duration) + 0.5)
					duration = '%s&nbsp;ms' % duration
			else:
				duration = startTime = '-'
			if abortRequest and requestID and requestID != myRequestID:
				checkbox = ('<input type="hidden" name="allIDs" value="%d">'
					'<input type="checkbox" name="selectedIDs" value="%d">'
					% (requestID, requestID))
			else:
				checkbox = '&nbsp;'
			if not requestID:
				requestID = '-'
			elif requestID == myRequestID:
				requestID = '<b>%s</b>' % requestID
			if not client:
				client = '-'
			if uri:
				uri = uri.replace('/', '/' + '<wbr>')
			else:
				uri = '-'
			wr('<tr><td align="right">', name,
				'</td><td align="right">', requestID,
				'</td><td>', startTime, '</td><td align="right">', duration,
				'</td><td>', client, '</td><td>', uri,
				'</td><td align="center">', checkbox, '</td></tr>')
		if activeThreads:
			wr('</table>')
		longIDs = ','.join(map(str, longIDs))
		wr('<input type="hidden" name="longIDs" value="%s">' % longIDs)
		wr('</form>')

		if threadCount > len(activeThreads):
			wr('<p>Idle threads waiting for requests: <b>%d</b></p>' %
				(threadCount - len(activeThreads)))
		wr('<p>Current time: %s</p>' % strtime(curTime))

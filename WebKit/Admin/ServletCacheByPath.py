from AdminPage import AdminPage
from string import join
from WebUtils.WebFuncs import HTMLEncode
from Queue import Queue


class ServletCacheByPath(AdminPage):
	'''
	This servlet displays, in a readable form, the internal data
	structure of the application known as the "servlet cache by path".

	This can be useful for debugging WebKit problems and interesting
	in general.
	'''

	def title(self):
		return 'Servlet Cache by Path'

	def writeContent(self):
		cache = self.application()._servletCacheByPath
		self.writeln(htCache(cache))


def htCache(cache):
	html = []
	ap = html.append

	keys = cache.keys()
	keys.sort()

	ap('%d paths' % len(keys))
	ap('<table align=center border=1 cellpadding=2 cellspacing=2>\n')

	for key in keys:
		ap('<tr> <td> %s </td> <td>' % key)
		ap(htRecord(cache[key]))
		ap('</td> </tr>')
	ap('</table>')

	return join(html, '')


def htRecord(record):
	html = []
	ap = html.append
	ap('<table border=1 width=100%>')
	keys = record.keys()
	keys.sort()
	for key in keys:
		htKey = HTMLEncode(key)

		# determine the HTML for the value
		value = record[key]
		htValue = None
		if hasattr(value, '__class__'):
			# check for special cases where we want a custom display
			if issubclass(value.__class__, Queue):
				htValue = htQueue(value)
		if not htValue:
			# the default is just the str() of the value
			htValue = HTMLEncode(str(value))

		ap('<tr> <td> %s </td> <td> %s </td> </tr>' % (htKey, htValue))
	ap('</table>')
	return join(html, '')


def htQueue(queue):
	return 'Queue: ' + HTMLEncode(str(queue.queue))
	
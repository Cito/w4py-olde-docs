from WebKit.Page import Page
import time
try:
	from mx import DateTime
except ImportError:
	try:
		import DateTime
	except ImportError:
		DateTime = None



cookieValues = [
	('onclose', 'ONCLOSE'),
	('expireNow', 'NOW'),
	('expireNever', 'NEVER'),
	('oneMinute', '+1m'),
	('oneWeek', '+1w'),
	('oneHourAndHalf', '+ 1h 30m'),
	('timeIntTenSec', time.time() + 10),
	('tupleOneYear', (time.localtime()[0] + 1,) + time.localtime()[1:]),
	]

if DateTime:
	cookieValues.extend([
		('dt2004', DateTime.DateTime(2004)),
		('dt2min', DateTime.TimeDelta(minutes=2)),
		('dt4minRelative', DateTime.RelativeDateTime(minutes=4)),
		])

cookieIndex = 1

class SetCookie(Page):

	def writeContent(self):
		global cookieIndex
		res = self.response()
		req = self.request()
		self.write('The time right now is:<br>\n')
		self.write(time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', time.gmtime()))
		self.write('<hr>\n')
		self.write('<h2>Cookies received:</h2>\n')
		for name, value in req.cookies().items():
			self.write('%s = %s <br>\n'
                                   % (repr(name), self.htmlEncode(value)))
		self.write('<hr>\n')
		for name, expire in cookieValues:
			res.setCookie(name, 'Value #%i' % cookieIndex, expires=expire)
			cookieIndex += 1
		self.write('<h2>Cookies being sent:</h2>\n')
		for name, cookie in res.cookies().items():
			self.write('%s sends:<br>\n' % repr(name))
			self.write('&nbsp;&nbsp;')
			self.write(self.htmlEncode(cookie.headerValue()))
			self.write('<br>\n')

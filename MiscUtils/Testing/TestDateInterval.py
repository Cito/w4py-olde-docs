import os
import unittest

import FixPath
from MiscUtils.DateInterval import *


class TestDateInterval(unittest.TestCase):

	def testTimeEncode(self):
		assert timeEncode(1) == '1s'
		assert timeEncode(60) == '1m'
		assert timeEncode(176403) == '2d1h3s'
		assert timeEncode(349380) == '4d1h3m'
		assert timeEncode(38898367) == '1y2b3w4d5h6m7s'

	def testTimeDecode(self):
		assert timeDecode('1s') == 1
		assert timeDecode('1h2d3s') == 176403
		assert timeDecode('2d1h3s') == 176403
		assert timeDecode('1h4d3m') == 349380
		assert timeDecode('3m4d1h') == 349380
		assert timeDecode('1y2b3w4d5h6m7s') == 38898367
		assert timeDecode('0y1b2w3d4h5m6s') == 4075506
		assert timeDecode('6s5m4h3d2w1b0y') == 4075506
		assert timeDecode('(3s-2d-1h)') == 176403
		try:
			timeDecode('1h5n')
		except ValueError, e:
			assert str(e) == 'Invalid unit of time: n'


if __name__ == '__main__':
	unittest.main()

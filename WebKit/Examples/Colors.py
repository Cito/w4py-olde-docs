import os
from ExamplePage import ExamplePage

class Colors(ExamplePage):
	"""Colors demo.

	This class is a good example of caching. The color table that
	this servlet creates never changes, so the servlet caches this in
	the _htColorTable attribute. The original version of this
	example did no caching and was 12 times slower.

	"""

	def __init__(self):
		ExamplePage.__init__(self)
		self._htColorTable = None

	def awake(self, trans):
		"""Set _bgcolor according to our field."""
		ExamplePage.awake(self, trans)
		self._bgcolor = ''
		self._bgcolorArg = ''
		req = self.request()
		if req.hasField('bgcolor'):
			self._bgcolor = req.field('bgcolor').strip()

	def htBodyArgs(self):
		"""Overridden to throw in the custom background color that the user can specify in our form."""
		bgcolor = self._bgcolor or 'white'
		return 'color="black" bgcolor="%s" ' \
			'style="color:black;background-color:%s"' % ((bgcolor,)*2)

	def writeContent(self):
		self.writeln('<div style="text-align:center">')
		self.write('''
			<h3>Color Table Demo</h3>
			<form>
				Background color: <input type="next" name="bgcolor" value="%s">
				<input type="submit" value="Go">
			</form>
		''' % (self._bgcolor))
		self.writeln(self.htColorTable())
		self.writeln('</div>')

	def htColorTable(self):
		if self._htColorTable is None:
			colorTable = ['<table cellpadding="4" cellspacing="4"'
				' style="margin-left:auto;margin-right:auto">']
			gamma = 2.2  # an approximation for today's CRTs, see "brightness =" below
			numSteps = 8
			steps = map(float, range(numSteps))
			denominator = float(numSteps-1)
			for r in steps:
				r = r/denominator
				for g in steps:
					g = g/denominator
					colorTable.append('<tr>\n')
					for b in steps:
						b = b/denominator
						color = '#%02x%02x%02x' % (r*255, g*255, b*255)
						# Compute brightness given RGB:
						brightness = (0.3*r**gamma + 0.6*g**gamma + 0.1*b**gamma)**(1/gamma)
						# We then use brightness to determine a good font color for high contrast:
						if brightness < 0.5:
							textcolor = 'white'
						else:
							textcolor = 'black'
						colorTable.append('<td style="background-color:%s;color:%s"'
							' onclick="document.forms[0].elements[0].value=\'%s\';'
							'document.forms[0].submit()">%s</td>\n'
							% (color, textcolor, color, color))
					colorTable.append('</tr>\n')
			colorTable.append('</table>')
			self._htColorTable = ''.join(colorTable)
		return self._htColorTable

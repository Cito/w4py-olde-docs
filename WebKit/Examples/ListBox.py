from ExamplePage import ExamplePage
from types import ListType


class ListBox(ExamplePage):
	"""List box example.

	This page provides a list box interface with controls
	for changing its size and adding and removing items.

	The source is a good example of how to use awake() and actions.

	"""

	def awake(self, transaction):
		ExamplePage.awake(self, transaction)
		sess = transaction.session()
		if not sess.hasValue('form'):
			sess.setValue('form', {
				'list':      [],
				'height':    10,
				'width':    250,
				'newCount':   1,
			})
		self._error = None

	def writeContent(self):
		sess = self.session()
		self.writeln('<div style="text-align:center">')
		if 0: # Debugging
			self.writeln('<p>fields = %s</p>' % self.htmlEncode(str(self.request().fields())))
			self.writeln('<p>vars = %s</p>' % self.htmlEncode(str(self.vars())))
		# Intro text is provided by our class' doc string:
		intro = self.__class__.__doc__.split('\n\n')
		self.writeln('<h2>%s</h2>' % intro.pop(0))
		for s in intro:
			self.writeln('<p>%s</p>' % s.replace('\n', '<br>'))
		if not self._error:
			self._error = '&nbsp;'
		self.writeln('<p style="color:red">%s</p>' % self._error)
		self.writeln('''
<form method="post">
<select multiple="yes" name="list" size="%(height)d"
style="width:%(width)dpt;text-align:center">
''' % sess.value('form'))
		index = 0
		vars = self.vars()
		for item in vars['list']:
			self.writeln('<option value="%d">%s</option>' % (index, self.htmlEncode(item['name'])))
			index += 1
		self.writeln('''
</select>
<p>
<input name="_action_new" type="submit" value="New">
<input name="_action_delete" type="submit" value="Delete">
&nbsp; &nbsp; &nbsp;
<input name="_action_taller" type="submit" value="Taller">
<input name="_action_shorter" type="submit" value="Shorter">
&nbsp; &nbsp; &nbsp;
<input name="_action_wider" type="submit" value="Wider">
<input name="_action_narrower" type="submit" value="Narrower">
</p>
</form>
</div>
''')

	def heightChange(self):
		return 1

	def widthChange(self):
		return 30


	## Commands ##

	def vars(self):
		"""Return a dictionary of values, stored in the session, for this page only."""
		return self.session().value('form')

	def new(self):
		vars = self.vars()
		vars['list'].append({'name': 'New item %d'%vars['newCount']})
		vars['newCount'] += 1
		self.writeBody()

	def delete(self):
		"""Delete the selected items in the list whose indices are passed in through the form."""
		vars = self.vars()
		req = self.request()
		if req.hasField('list'):
			indices = req.field('list')
			if type(indices) is not ListType:
				indices = [indices]
			indices = map(int, indices) # convert strings to ints
			indices.sort() # sort...
			indices.reverse() # in reverse order
			# remove the objects:
			for index in indices:
				del vars['list'][index]
		else:
			self._error = 'You must select a row to delete.'
		self.writeBody()

	def taller(self):
		vars = self.vars()
		vars['height'] += self.heightChange()
		self.writeBody()

	def shorter(self):
		vars = self.vars()
		if vars['height'] > 2:
			vars['height'] -= self.heightChange()
		self.writeBody()

	def wider(self):
		vars = self.vars()
		vars['width'] += self.widthChange()
		self.writeBody()

	def narrower(self):
		vars = self.vars()
		if vars['width'] >= 60:
			vars['width'] -= self.widthChange()
		self.writeBody()


	## Actions ##

	def actions(self):
		return ExamplePage.actions(self) + \
			['new', 'delete', 'taller', 'shorter', 'wider', 'narrower']

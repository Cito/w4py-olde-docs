from ExamplePage import ExamplePage
from WebUtils.WebFuncs import HTMLEncode
import string
from types import ListType


class Item:
	''' Items are the objects that are added, deleted and edited by the
		user in this example. '''
	def __init__(self, name):
		self._name = name

	def name(self):
		return self._name


class ListBox(ExamplePage):
	'''
	This page provides a list box interface with controls for changing
	it's size and adding and removing items.

	The source is a good example of how to use awake() and actions.
	'''

	def awake(self, transaction):
		ExamplePage.awake(self, transaction)
		sess = transaction.session()
		if not sess.hasValue('form'):
			sess.setValue('form', {
				'list':       [],
				'height':     10,
				'width':     250,
				'newCount':    1,
			} )
		self._error = None

	def writeBody(self):
		sess = self.session()

		# Debugging
		if 0:
			self.writeln('<br>fields = ', HTMLEncode(str(self.request().fields())))
			self.writeln('<br>vars = ', HTMLEncode(str(self.vars())))
			self.writeln('<p> <br>')

		# Intro text is provided by our class' doc string
		self.writeln('<center>', string.replace(self.__class__.__doc__, '\n', '<br>'), '</center>')

		if not self._error:
			self._error = '&nbsp;'
		self.writeln('<p><center><font color=red>%s</font></center>' % self._error)
		self.writeln('''
<center>
<form method=post>
<select multiple name=list size=%(height)d width=%(width)d>
''' % sess.value('form'))
		index = 0
		vars = self.vars()
		for item in vars['list']:
			self.writeln('<option value=%d>%s</option>' % (index, HTMLEncode(item.name())))
			index = index + 1

		self.writeln('''
</select>

<br>

<input name=_action_ type=submit value=New>
<!--
<input name=_action_ type=submit value=Edit>
<input name=_action_ type=submit value=View>
-->
<input name=_action_ type=submit value=Delete>

<br>

<input name=_action_ type=submit value=Taller>
<input name=_action_ type=submit value=Shorter>

<br>

<input name=_action_ type=submit value=Wider>
<input name=_action_ type=submit value=Narrower>
<br><i><b>Wider</b> and <b>Narrower</b> work on Netscape, but not on IE.</i>

</form>
</center>
''')

	def heightChange(self):
		return 1

	def widthChange(self):
		return 30


	## Commands ##

	def vars(self):
		''' Returns a dictionary of values, stored in the session, for this page only. '''
		return self.session().value('form')

	def new(self, trans):
		vars = self.vars()
		vars['list'].append(Item('New item %d'%vars['newCount']))
		vars['newCount'] = vars['newCount'] + 1
		self.writeBody()

	def edit(self, trans):
		self.writeBody() # @@ 2000-06-01 ce: not implemented

	def view(self, trans):
		self.writeBody() # @@ 2000-06-01 ce: not implemented

	def delete(self, trans):
		''' Delete the selected items in the list, whose indices are passed in through the form. '''
		vars = self.vars()
		req = trans.request()
		if req.hasField('list'):
			indices = req.field('list')
			if type(indices) is not ListType:
				indices = [indices]
			indices = map(lambda x: int(x), indices) # convert strings to ints
			indices.sort() # sort...
			indices.reverse() # in reverse order
			# remove the objects
			for index in indices:
				del vars['list'][index]
		else:
			self._error = 'You must select a row to delete.'
		self.writeBody()

	def taller(self, trans):
		vars = self.vars()
		vars['height'] = vars['height'] + self.heightChange()
		self.writeBody()

	def shorter(self, trans):
		vars = self.vars()
		if vars['height']>2:
			vars['height'] = vars['height'] - self.heightChange()
		self.writeBody()

	def wider(self, trans):
		vars = self.vars()
		vars['width'] = vars['width'] + self.widthChange()
		self.writeBody()

	def narrower(self, trans):
		vars = self.vars()
		if vars['width']>=60:
			vars['width'] = vars['width'] - self.widthChange()
		self.writeBody()


	## Actions ##

	def methodNameForAction(self, name):
		''' Our button titles are captialized like 'New', but our methods are lower case like 'new'. So we implement this method to convert action names to lowercase. '''
		return string.lower(name)

	def actions(self):
		return ExamplePage.actions(self) + ['new', 'edit', 'view', 'delete', 'taller', 'shorter', 'wider', 'narrower']

from ExamplePage import ExamplePage


class Error(ExamplePage):

	def title(self):
		return 'Error raising Example'

	def writeContent(self):
		error = self.request().field('error', None)
		if error:
			msg = 'You clicked that button!'
			if error.startswith('String'):
				error = msg
			elif error.startswith('System'):
				error = SystemError(msg)
			else:
				error = StandardError(msg)
			self.writeln('<p>About to raise an error...</p>')
			raise error
		self.writeln('''<h1>Error Test</h1>
<form action="Error">
<p><select name="error" size="1">
<option selected>StandardError</option>
<option>SystemError</option>
<option>String error (old)</option>
</select>
<input type="submit" value="Don't click this button!"></p>
</form>''')

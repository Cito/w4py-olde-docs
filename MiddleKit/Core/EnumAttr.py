from Attr import Attr


class EnumAttr(Attr):

	def __init__(self, dict):
		Attr.__init__(self, dict)
		# We expect than an 'Enums' key holds the enumeration values
		enums = self['Enums']
		enums = enums.split(',')
		enums = [enum.strip() for enum in enums]
		self._enums = enums

	def enums(self):
		return self._enums

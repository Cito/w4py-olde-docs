from Attr import Attr


class ListAttr(Attr):
	"""
	This is an attribute that refers to a set of other user-defined objects.
	It cannot include basic data types or instances of classes that are not part of the object model.
	"""

	def __init__(self, dict):
		Attr.__init__(self, dict)
		self._className = dict['Type'].split()[-1]
		if dict.has_key('backRefAttr'):
			self._backRefAttr = dict['backRefAttr']
		else:
			self._backRefAttr = None
		
		# @@ 2000-11-25 ce: check that the class really exists
		if self.get('Max') is not None:
			self['Max'] = int(self['Max'])
		if self.get('Min') is not None:
			self['Min'] = int(self['Min'])

	def className(self):
		""" Returns the name of the base class that this obj ref attribute points to. """
		return self._className

	def backRefAttrName(self):
		''' Returns the name of the back-reference attribute in the referenced 
		class.  It is necessary to be able to override the default back ref 
		to create data structures like trees, in which a Middle object might
		reference a parent and multiple children, all of the same class as 
		itself.
		'''
		if self._backRefAttr:
			return self._backRefAttr
		else:
			classname = self.klass().name()
			return classname[0].lower() + classname[1:]

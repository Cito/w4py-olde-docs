

class CanContainer:

	def __init__(self):
		self._Cans={}

	def getCan(self, CanID, *args, **kwargs):
		debug = 0
		if debug: print __file__,"getCan: ", CanID 
		try:
			return self._Cans.get(CanID, None)
		except AttributeError:
			#The init function for this class won't get called.  So an AttributeError means self._Cans doesn't exist yet.
			self._Cans={}
			return None			

	def delCan(self, CanID):
		del self._Cans[CanID]

	def cans(self):
		"""List the cans stored in this container"""
		if self.__dict__.has_key('_Cans'):
			return self._Cans.keys()
		return None

	def setCan(self,ID,item):
		"""Adds a new can to this container"""
		if not self.__dict__.has_key("_Cans"):
			self._Cans={}
		self._Cans[ID]=item

	def _delCans(self):
		""" Deleted all cans in this container """
		if self.cans():
			for i in self.cans():
				self.delCan(i)

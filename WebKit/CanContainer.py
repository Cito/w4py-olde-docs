

class CanContainer:

	def __init__(self):
		self._Cans={}

	def getCan(self, CanID):
		try:
			return self._Cans.get(CanID)
		except AttributeError:
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
		for i in self.cans():
			self.delCan(i)


class LocationCan:
    """ This is a simple Can to test that the system works."""
    def __init__(self):
	self._locationList=[]
	

    def addLocation(self,location):
	self._locationList.append(location)

    def locationList(self):
	return self._locationList

	


from WebKit.Page import Page
import string


class PSPPage(Page):

    def __init__(self):
	#self.parent = string.split(str(self.__class__.__bases__[0]),'.')[1]
	#print self.parent
	self.parent=Page
	self.parent.__init__(self)

    def awake(self, trans):
	self.parent.awake(self, trans)
	self.out = trans.response()






from UserManager import UserManager
from Role import Role
from MiscUtils import NoDefault


class RoleUserManager(UserManager):
	'''
	RoleUserManager adds the functionality of keeping a dictionary mapping names to role instances. Several accessor methods are provided for this.
	'''


	baseOfRoleUserManager = UserManager

	## Init ##

	def __init__(self, userClass=None):
		self.baseOfRoleUserManager.__init__(self, userClass)
		self._roles = {}


	## Settings ##

	def userClass(self):
		''' Returns the userClass. This implementation overrides the inherited one to make RoleUser the default user class. '''
		if self._userClass is None:
			from RoleUser import RoleUser
			self.setUserClass(RoleUser)
		return self._userClass


	## Roles ##

	def addRole(self, role):
		assert isinstance(role, Role)
		name = role.name()
		assert not self._roles.has_key(name)
		self._roles[name] = role

	def role(self, name, default=NoDefault):
		if default is NoDefault:
			return self._roles[name]
		else:
			return self._roles.get(name, default)

	def hasRole(self, name):
		return self._roles.has_key(name)

	def delRole(self, name):
		del self._roles[name]

	def roles(self):
		return self._roles

	def clearRoles(self):
		self._roles = {}

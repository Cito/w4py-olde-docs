import os, sys
sys.path.insert(1, os.path.abspath('../..'))
import UserKit
from MiscUtils import unittest

import shutil

# @@ 2001-02-25 ce: We might consider breaking this file up pretty soon


class UserManagerTest(unittest.TestCase):

	def setUp(self):
		from UserKit.UserManager import UserManager
		self.mgr = UserManager()

	def checkSettings(self):
		mgr = self.mgr
		value = 5.1

		mgr.setModifiedUserTimeout(value)
		assert mgr.modifiedUserTimeout()==value

		mgr.setCachedUserTimeout(value)
		assert mgr.cachedUserTimeout()==value

		mgr.setActiveUserTimeout(value)
		assert mgr.activeUserTimeout()==value

	def checkUserClass(self):
		mgr = self.mgr
		from UserKit.User import User
		class SubUser(User): pass
		mgr.setUserClass(SubUser)
		assert mgr.userClass()==SubUser
		class Poser: pass
		self.assertRaises(Exception, mgr.setUserClass, Poser)

	def tearDown(self):
		self.mgr.shutDown()
		self.mgr = None


class UserManagerToSomewhereTest(UserManagerTest):

	def checkUsers(self):
		mgr = self.mgr
		user = self.user = mgr.createUser('foo', 'bar')
		assert user.manager()==mgr
		assert user.name()=='foo'
		assert user.password()=='bar'
		assert not user.isActive()
		assert mgr.userForSerialNum(user.serialNum())==user
		assert mgr.userForExternalId(user.externalId())==user
		assert mgr.userForName(user.name())==user

		users = mgr.users()
		assert len(users)==1
		assert users[0]==user, 'users[0]=%r, user=%r' % (users[0], user)
		assert len(mgr.activeUsers())==0
		assert len(mgr.inactiveUsers())==1

		# login
		user2 = mgr.login(user, 'bar')
		assert user==user2
		assert user.isActive()
		assert len(mgr.activeUsers())==1
		assert len(mgr.inactiveUsers())==0

		# logout
		user.logout()
		assert not user.isActive()
		assert mgr.numActiveUsers()==0

		# login via user
		result = user.login('bar')
		assert result==user
		assert user.isActive()
		assert mgr.numActiveUsers()==1

		# logout via user
		user.logout()
		assert not user.isActive()
		assert mgr.numActiveUsers()==0

		# login a 2nd time, but with bad password
		user.login('bar')
		user.login('rab')
		assert not user.isActive()
		assert mgr.numActiveUsers()==0


class UserManagerToFileTest(UserManagerToSomewhereTest):

	def setUp(self):
		from UserKit.UserManagerToFile import UserManagerToFile
		self.mgr = UserManagerToFile()
		path = 'Users'
		if os.path.exists(path):
			shutil.rmtree(path, ignore_errors=1)
		os.mkdir(path)
		self.mgr.setUserDir(path)

	def tearDown(self):
		path = 'Users'
		if os.path.exists(path):
			shutil.rmtree(path, ignore_errors=1)


class UserManagerToMiddleKitTest(UserManagerToSomewhereTest):

	def checkUserClass(self):
		pass

	def makeModel(self):
		''' Constructs and returns a MiddleKit model for use with UserKit. '''

		from MiddleKit.Core.Model import Model
		from MiddleKit.Core.Klasses import Klasses
		from MiddleKit.Core.Klass import Klass
		from MiddleKit.Core.StringAttr import StringAttr
		klass = Klass()
		klass.readDict({'Class': 'UserForMKTest'})
		klass.addAttr(StringAttr({
			'Name': 'name',
			'Type': 'string',
			'isRequired': 1,
		}))
		klass.addAttr(StringAttr({
			'Name': 'password',
			'Type': 'string',
			'isRequired': 1,
		}))
		klass.addAttr(StringAttr({
			'Name': 'externalId',
			'Type': 'string',
			'isRequired': 0,
		}))
		model = Model()
		model.setName(self.__class__.__name__)
		klasses = model.klasses()
		klasses.addKlass(klass)
		klasses.awakeFromRead() # @@ 2001-02-17 ce: a little weird
		return model

	def setUp(self):
		model = self.makeModel()
		from MiddleKit.Design.Generate import Generate
		generate = Generate().generate
		# @@ 2001-02-18 ce: woops: hard coding MySQL
		generate(
			pyClass='MySQLPythonGenerator',
			model=model,
			outdir='.')
		generate(
			pyClass='MySQLSQLGenerator',
			model=model,
			outdir='.')
		print
		os.system('mysql < Create.sql')

		from MiddleKit.Run.MySQLObjectStore import MySQLObjectStore
		store = MySQLObjectStore()
		store.setSQLEcho(None) # @@ 2001-02-19 ce: this will probably be the MK default shortly and we won't need this
		store.setModel(model)

		from MiddleKit.Run.MiddleObject import MiddleObject
		from UserKit.UserManagerToMiddleKit import UserManagerToMiddleKit
		from UserForMKTest import UserForMKTest
		assert issubclass(UserForMKTest, MiddleObject)
		from UserKit.User import User
		UserForMKTest.__bases__ = UserForMKTest.__bases__ + (User,)
		assert issubclass(UserForMKTest, MiddleObject)
		assert issubclass(UserForMKTest, MiddleObject)

		def __init__(self, manager, name, password):
			base1 = self.__class__.__bases__[0]
			base2 = self.__class__.__bases__[1]
			base1.__init__(self)
			base2.__init__(self, manager=manager, name=name, password=password)

		UserForMKTest.__init__ = __init__
		self.mgr = UserManagerToMiddleKit(userClass=UserForMKTest, store=store)

	def tearDown(self):
		# clean out generated files
		filenames = ['UserForMKTest.py', 'UserForMKTest.pyc', 'GenUser.py', 'GenUser.pyc', 'Create.sql', 'InsertSamples.sql', 'Info.text']
		for filename in filenames:
			if os.path.exists(filename):
				os.remove(filename)
		self.mgr = None


def makeTestSuite():
	suite1 = unittest.makeSuite(UserManagerTest, 'check')
	suite2 = unittest.makeSuite(UserManagerToFileTest, 'check')
	suite3 = unittest.makeSuite(UserManagerToMiddleKitTest, 'check')
	return unittest.TestSuite((suite1, suite2, suite3))


if __name__=='__main__':
	runner = unittest.TextTestRunner(stream=sys.stdout)
	unittest.main(defaultTest='makeTestSuite', testRunner=runner)

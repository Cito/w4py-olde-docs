"""Unittests for the Role classes."""

import os
import sys
import unittest

testDir = os.path.dirname(os.path.abspath(__file__))
webwarePath = os.path.dirname(os.path.dirname(testDir))
if sys.path[0] != webwarePath:
    sys.path.insert(0, webwarePath)


class BasicRoleTest(unittest.TestCase):
    """Tests for the basic role class."""

    def roleClasses(self):
        """Return a list of all Role classes for testing."""
        from UserKit.Role import Role
        from UserKit.HierRole import HierRole
        return [Role, HierRole]

    def testA_RoleBasics(self):
        """Invoke testRole() with each class returned by roleClasses."""
        for roleClass in self.roleClasses():
            self.checkRoleClass(roleClass)

    def checkRoleClass(self, roleClass):
        role = roleClass('foo', 'bar')
        assert role.name() == 'foo'
        assert role.description() == 'bar'
        assert str(role) == 'foo'

        role.setName('x')
        assert role.name() == 'x'

        role.setDescription('y')
        assert role.description() == 'y'

        assert role.playsRole(role)


class HierRoleTest(unittest.TestCase):
    """Tests for the hierarchical role class."""

    def testHierRole(self):
        from UserKit.HierRole import HierRole as hr
        animal = hr('animal')
        eggLayer = hr('eggLayer', None, [animal])
        furry = hr('furry', None, [animal])
        snake = hr('snake', None, [eggLayer])
        dog = hr('dog', None, [furry])
        platypus = hr('platypus', None, [eggLayer, furry])
        vegetable = hr('vegetable')

        roles = locals()
        del roles['hr']
        del roles['self']

        # The tests below are one per line.
        # The first word is the role name. The rest of the words
        # are all the roles it plays (besides itself).
        tests = '''\
            eggLayer, animal
            furry, animal
            snake, eggLayer, animal
            dog, furry, animal
            platypus, eggLayer, furry, animal'''

        tests = [test.split(', ') for test in tests.splitlines()]

        # Strip names
        # Can we use a compounded/nested list comprehension for this?
        oldTest = tests
        tests = []
        for test in oldTest:
            test = [name.strip() for name in test]
            tests.append(test)

        # Now let's actually do some testing...
        for test in tests:
            role = roles[test[0]]
            assert role.playsRole(role)

            # Test that the role plays all the roles listed
            for name in test[1:]:
                playsRole = roles[name]
                assert role.playsRole(playsRole)

            # Now test that the role does NOT play
            # any of the other roles not listed
            otherRoles = roles.copy()
            for name in test:
                del otherRoles[name]
            for name in otherRoles.keys():
                assert not role.playsRole(roles[name])


if __name__ == '__main__':
    unittest.main()
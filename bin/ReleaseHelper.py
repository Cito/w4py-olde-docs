#!/usr/bin/env python
"""
Helps with cutting Python releases.

This script creates a tar file named Webware-VER.tar.gz from a live CVS
workspace. The workspace is updated, but is not destroyed in the process.
The workspace should NOT have had install.py run on it, or your distro
will end up with generated docs.

To run:

  > ReleaseHelper.py

- The version number is taken from Webware/Properties.py like you would
  expect.
- You don't have to be in the current directory:
    > bin/ReleaseHelper.py
    > Webware/bin/ReleaseHelper.py
- This script only works on posix. Releases are not created on Windows
  because permissions and EOLs can be problematic for other platforms.

For more information, see the Release Procedures in the Webware docs.

TO DO

  - Using ProperitesObject, this program could suggest a version string
    from the Webware version.
"""

import os, sys, time


class ReleaseHelper:

	def main(self):
		self.writeHello()
		self.checkPlatform()
		self.readArgs()

		progPath = os.path.join(os.getcwd(), sys.argv[0])  # the location of this script
		webwarePath = os.path.dirname(os.path.dirname(progPath))  # because we're in Webware/bin/
		parentPath = os.path.dirname(webwarePath)  # where the tarball will land

		self.chdir(webwarePath)

		if os.path.exists('_installed'):
			self.error('This Webware has already been installed.')

		from MiscUtils.PropertiesObject import PropertiesObject
		props = PropertiesObject(os.path.join(webwarePath, 'Properties.py'))
		ver = props['versionString']
		print 'Webware version is:', ver

		self.run('cvs update -dP')  # get new directories; prune empty ones

		try:
			tempName = os.tmpnam()
			os.mkdir(tempName)
			self.run('cp -pr %s %s' % (webwarePath, tempName))

			# Get rid of CVS files
			self.run("find %s -name '.cvs*' -exec rm {} \;" % tempName)
			self.run("rm -rf `find %s -name CVS -print`" % tempName)

			self.chdir(tempName)
			pkgName = 'Webware-%s.tar.gz' % ver
			self.run('tar czf %s Webware' % pkgName)

			# Put the results next to the Webware directory
			self.run('cp %s %s' % (pkgName, parentPath))

			assert os.path.exists(os.path.join(parentPath, pkgName))

		finally:
			# Clean up
			self.run('rm -rf %s' % tempName)

		self.writeGoodBye(locals())

	def writeHello(self):
		print 'Webware for Python'
		print 'Release Helper'
		print

	def checkPlatform(self):
		if os.name!='posix':
			print 'This script only runs on posix. Your op sys is %s.' % os.name
			print 'Webware release are always created on posix machines.'
			print 'These releases work on both posix and MS Windows.'
			self.error()

	def readArgs(self):
		args = {}
		for arg in sys.argv[1:]:
			try:
				name, value = arg.split('=')
			except ValueError:
				self.error('Invalid argument: %s' % arg)
			args[name] = value
		self.args = args

	def error(self, msg=''):
		if msg:
			print 'ERROR: %s' % msg
		sys.exit(1)

	def chdir(self, path):
		print 'chdir %s' % path
		os.chdir(path)

	def run(self, cmd):
		""" Runs an arbitrary UNIX command. """
		print 'cmd>', cmd
		results = os.popen(cmd).read()
		print results

	def writeGoodBye(self, vars):
		print
		print 'file: %(pkgName)s' % vars
		print 'dir:  %(parentPath)s' % vars
		print 'size: %i' % os.path.getsize(os.path.join(vars['parentPath'], vars['pkgName']))
		print
		print 'Success.'
		print


if __name__=='__main__':
	ReleaseHelper().main()

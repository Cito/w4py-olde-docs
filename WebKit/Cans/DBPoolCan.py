"""

This is an example of how to do Application level DB connection pooling and make it easily available to servlets.

"""

from MiscUtils.DBPool import *

## First we import the DB API module we will be using
import pgdb  #use the standard PostGreSQL module

## Now we set the connection parameters
connargs = () ##('localhost:testdb',)  #straight parameters, in the form of a tuple
connkwargs = {'host':'localhost', 'database':'testdb'}   #any keyword arguments I want to pass in

## Maximum connections to pool
maxconns = 10

class DBPoolCan(DBPool):

	def __init__(self):
		apply(DBPool.__init__, (self, pgdb, maxconns) + connargs, connkwargs)
		print "Starting new DBPool"

## Thats it.
## Here's how to use it in a servlet
## First we get the Application wide instance of the Can using Page.getCan (or Servlet.getCan)
## The parameters are:
## #1 'dbCan'  This is the name that application stores this instance as.  Always use the same name, or there will be multiple instance of this class instatiated
## #2 'WebKit.Cans.DBPoolCan'  the full package name of this file
## #3 'application'  the container we want this can instance stored in.  Should always be 'application' for this Can.
##
## dbcan = self.getCan("dbcan","WebKit.Cans.DBPoolCan", "application") 
##
## Now we ask the DBPool module to give us a connection
##
## conn = dbcan.getConnection()
##
## Now we use it.  It will be returned automatically, but commit will not be called for you!
##
## cursor = conn.cursor()
## cursor.execute('SELECT * FROM MYTABLE')


"""Session store using the Memcached memory object caching system."""

from warnings import warn
try:
    from cPickle import HIGHEST_PROTOCOL as maxPickleProtocol
except ImportError:
    from pickle import HIGHEST_PROTOCOL as maxPickleProtocol

try:
    import memcache
except Exception:
    raise ImportError("For using Memcached sessions,"
        " python-memcached must be installed.")

from MiscUtils import NoDefault

from SessionStore import SessionStore

debug = False


class SessionMemcachedStore(SessionStore):
    """A session store using Memached.

    Stores the sessions in a single Memcached store using 'last write wins'
    semantics. This increases fault tolerance and allows server clustering.
    In clustering configurations with concurrent writes for the same
    session(s) the last writer will always overwrite the session.

    Cleaning/timing out of sessions is performed by Memcached itself
    since no one app server can know about the existence of all sessions or
    the last access for a given session. Besides it is built in Memcached
    functionality. Consequently, correct sizing of Memcached is necessary
    to hold all user's session data.

    The keys are prefixed with a configurable namespace, allowing you to
    store other data in the same Memcached system.

    You need to install python-memcached to be able to use this module:
    http://www.tummy.com/Community/software/python-memcached/
    You also need a Memcached server: http://memcached.org

    Contributed by Steve Schwarz, March 2010.
    Improvements by Christoph Zwerschke, April 2010.

    """

    ## Init ##

    def __init__(self, app):
        SessionStore.__init__(self, app)

        # the list of memcached servers
        self._servers = app.setting('MemcachedServers', ['localhost:11211'])

        # timeout in seconds
        self._sessionTimeout = app.setting(
            'SessionTimeout', 180) * 60

        # the memcached "namespace" used by our store
        # you can add an integer counter for expiration
        self._namespace = app.setting(
            'MemcachedNamespace', 'WebwareSession') or ''
        if self._namespace:
            self._namespace += '_'
        self._useCounter = app.setting('MemcachedCounter', True)

        # when trying to iterate over the Memcached store,
        # you can trigger an error or a warning
        self._onIteration = app.setting('MemcachedOnIteration', 'Warning')

        self._client = memcache.Client(self._servers,
            debug=debug, pickleProtocol=maxPickleProtocol)

        try:
            self._counter = self.getCounter()
        except ValueError, exc:
            print "Warning: Could not get memcache counter: %s" % exc
            self._useCounter = None


    ## Access ##

    def __len__(self):
        """Return the number of sessions in the store.

        Not supported by Memcached (see FAQ for explanation).

        """
        if debug:
            print ">> len()"
        return len(self.keys())

    def __getitem__(self, key):
        """Get a session item, reading it from the store."""
        if debug:
            print ">> getitem(%s)" % key
        # returns None if key non-existent or no server to contact
        try:
            value = self._client.get(self.mcKey(key))
        except Exception:
            value = None
        if value is None:
            # SessionStore expects KeyError when no result
            raise KeyError(key)
        return value

    def __setitem__(self, key, item):
        """Set a session item, writing it to the store."""
        if debug:
            print ">> setitem(%s, %s)" % (key, item)
        try:
            if not self._client.set(self.mcKey(key), item,
                    time=self._sessionTimeout):
                raise ValueError("Setting value in the memcache failed.")
        except Exception, exc:
            # Not able to store the session is a failure
            print "Error saving session '%s' to memcache: %s" % (key, exc)
            self.application().handleException()

    def __delitem__(self, key):
        """Delete a session item from the store.

        Note that in contracts with SessionFileStore,
        not finding a key to delete isn't a KeyError.

        """
        if debug:
            print ">> delitem(%s)" % key
        session = self[key]
        if not session.isExpired():
            session.expiring()
        try:
            if not self._client.delete(self.mcKey(key)):
                raise ValueError("Deleting value from the memcache failed.")
        except Exception, exc:
            # Not able to delete the session is a failure
            print "Error deleting session '%s' from memcache: %s" % (key, exc)
            self.application().handleException()

    def __contains__(self, key):
        """Check whether the session store has a given key."""
        if debug:
            print ">> contains(%s)" % key
        try:
            return self._client.get(self.mcKey(key)) is not None
        except Exception:
            return False

    def __iter__(self):
        """Return an iterator over the stored session keys.

        Not supported by Memcached (see FAQ for explanation).

        """
        if debug:
            print ">> iter()"
        onIteration = self._onIteration
        if onIteration:
            err = 'Memcached does not support iteration.'
            if onIteration == 'Error':
                raise NotImplementedError(err)
            else:
                warn(err)
        return iter([])

    def keys(self):
        """Return a list with the keys of all the stored sessions.

        Not supported by Memcached (see FAQ for explanation).

        """
        if debug:
            print ">> keys()"
        return [key for key in self]

    def clear(self):
        """Clear the session store, removing all of its items.

        Not really supported by Memcached (keys expire automatically),
        but we emulate this by incrementing our namespace counter.

        """
        if debug:
            print ">> clear()"
        if self._useCounter:
            self._counter = self.incrCounter()
        else:
            if self._onIteration:
                err = 'Set MemcachedCounter to allow expiring the whole store.'
                if self._onIteration == 'Error':
                    raise NotImplementedError(err)
                else:
                    warn(err)

    def setdefault(self, key, default=None):
        """Return value if key available, else default (also setting it)."""
        if debug:
            print ">> setdefault(%s, %s)" % (key, default)
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def pop(self, key, default=NoDefault):
        """Return value if key available, else default (also remove key)."""
        if debug:
            print ">> pop(%s, %s)" % (key, default)
        if default is NoDefault:
            value = self[key]
            del self[key]
            return value
        else:
            try:
                value = self[key]
            except KeyError:
                return default
            else:
                del self[key]
                return value


    ## Application support ##

    def storeSession(self, session):
        """Save potentially changed session in the store."""
        if debug:
            print ">> storeSession(%s)" % session
        self[session.identifier()] = session

    def storeAllSessions(self):
        """Permanently save all sessions in the store.

        Should be used (only) when the application server is shut down.
        This closes the connection to the Memcached servers.

        """
        if debug:
            print ">> storeAllSessions()"
        self._client.disconnect_all()

    def cleanStaleSessions(self, task=None):
        """Clean stale sessions.

        Memcached does this on its own, so we do nothing here.

        """
        if debug:
            print ">> cleanStaleSessions()"


    ## Auxiliary methods ##

    def mcKey(self, key):
        """Create the real key with namespace to be used with Memcached."""
        if self._useCounter:
            return '%s%d_%s' % (self._namespace, self._counter, key)
        else:
            return '%s%s' % (self._namespace, key)

    def counterKey(self):
        """Create the key used for the namespace counter."""
        return '%s0_NamespaceCounter' % self._namespace

    def getCounter(self):
        """Get the current Memcached namespace counter."""
        if self._useCounter:
            counterKey = self.counterKey()
            counter = self._client.get(counterKey)
            if counter is None:
                self.setCounter(1)
                counter = self._client.get(counterKey)
                if counter != 1:
                    raise ValueError("Could not reset memcache counter")
            if debug:
                print ">> counter() = %d" % counter
            return counter

    def setCounter(self, counter):
        """Set a new Memcached namespace counter."""
        if self._useCounter:
            if debug:
                print ">> setcounter(%d)" % counter
            if self._client.set(self.counterKey(), counter, time=0):
                raise ValueError("Could not set memcache counter")

    def incrCounter(self):
        """Increment the Memcached namespace counter."""
        if self._useCounter:
            return self._client.incr(self.counterKey())

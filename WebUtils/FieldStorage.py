"""FieldStorage.py

This module defines a subclass of the standard Python cgi.FieldStorage class
with an extra method that will allow a FieldStorage to parse a query string
even in a POST request.

"""

import cgi, os, urllib


class FieldStorage(cgi.FieldStorage):

    def __init__(self, fp=None, headers=None, outerboundary="",
            environ=os.environ, keep_blank_values=False, strict_parsing=False):
        self._environ = environ
        cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
            environ, keep_blank_values, strict_parsing)

    def parse_qs(self):
        """Explicitly parse the query string, even if it's a POST request."""
        method = self._environ.get('REQUEST_METHOD', '').upper()
        if method in ('GET', 'HEAD'):
            return # bail because cgi.FieldStorage already did this
        qs = self._environ.get('QUERY_STRING')
        if not qs:
            return # bail if no query string

        r = {}
        for name_value in qs.split('&'):
            nv = name_value.split('=', 2)
            if len(nv) != 2:
                if self.strict_parsing:
                    raise ValueError('bad query field: %r' % (name_value,))
                continue
            name = urllib.unquote(nv[0].replace('+', ' '))
            value = urllib.unquote(nv[1].replace('+', ' '))
            if len(value) or self.keep_blank_values:
                if name in r:
                    r[name].append(value)
                else:
                    r[name] = [value]

        # Only append values that aren't already in the FieldStorage's keys;
        # this makes POSTed vars override vars on the query string.
        if not self.list:
            # This makes sure self.keys() are available, even
            # when valid POST data wasn't encountered.
            self.list = []
        for key in r:
            if key not in self:
                for value in r[key]:
                    self.list.append(cgi.MiniFieldStorage(key, value))

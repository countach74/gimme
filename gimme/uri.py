from urlparse import parse_qs
import re
import urllib


class QueryValue(list):
    def __init__(self, value=[]):
        list.__init__(self, value)

    def __str__(self):
        return self[0]

    def __repr__(self):
        return '<QueryValue(%s)>' % ', '.join(self)

    def __eq__(self, other):
        if isinstance(other, str) and len(self) == 1:
            return self[0] == other
        else:
            return list.__eq__(self, other)

    def __add__(self, other):
        if not isinstance(other, list):
            other = [other]
        copy = list(self)
        return QueryValue(copy + other)

    def __sub__(self, other):
        if not isinstance(other, list):
            other = [other]
        temp = list(self)
        for i in other:
            temp.remove(i)
        return QueryValue(temp)

    def __iadd__(self, other):
        if not isinstance(other, list):
            other = [other]
        return list.__iadd__(self, other)

    def __isub__(self, other):
        if not isinstance(other, list):
            other = [other]
        for i in other:
            self.remove(i)
        return self


class QueryString(object):
    _reserved_attrs = ('_query_string', '_quote_plus', '_parsed')

    def __init__(self, query_string, quote_plus=False):
        self._query_string = query_string
        self._quote_plus = quote_plus
        self._parsed = self._parse_qs(query_string)

    def __repr__(self):
        return 'QueryString(%s)' % self._parsed

    def __bool__(self):
        return bool(self._parsed)

    def __str__(self):
        result = []
        encode = urllib.quote_plus if self._quote_plus else urllib.quote
        for k, v in self._parsed.iteritems():
            for i in v:
                result.append('%s=%s' % (k, encode(i)))
        return '&'.join(result)

    def __getattr__(self, key):
        if key not in QueryString._reserved_attrs:
            try:
                return self._parsed[key]
            except KeyError, e:
                raise AttributeError(key)
        else:
            return object.__getattr__(self, key)

    def __setattr__(self, key, value):
        if key not in QueryString._reserved_attrs:
            if key not in self._parsed:
                self._parsed[key] = QueryValue([value])
        else:
            return object.__setattr__(self, key, value)

    def __getitem__(self, key):
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __delitem__(self, key):
        del(self._parsed[key])

    def __contains__(self, key):
        return key in self._parsed

    def __iter__(self):
        for i in self._parsed:
            yield i

    def _parse_qs(self, qs):
        temp = parse_qs(qs)
        for k, v in temp.items():
            temp[k] = QueryValue(v)
        return temp
    
    def iteritems(self):
        for i in self:
            yield (i, self[i])

    def items(self):
        return list(self.iteritems())


class URI(object):
    _pattern = re.compile('^([a-zA-Z0-9]+)?:?(\/\/)?([^\/?#]*)([^?]*)\??([^#]+)?#?(.*)$')

    def __init__(self, uri, escape_plus=False):
        self._uri = uri
        self._escape_plus = escape_plus

        match = self._pattern.match(uri)

        if not match:
            raise ValueError("Could not create GetHelper object from this string.")

        self.protocol = match.group(1)
        self.hostname = match.group(3)
        self.path = match.group(4)
        self.query_string = match.group(5) or ''
        self.hash = match.group(6) or ''

        self.query_params = QueryString(self.query_string)
        self.hash_params = QueryString(self.hash)

    def get_query_string(self):
        return str(self.query_params)

    def get_hash_string(self):
        if self.hash_params:
            return str(self.hash_params)
        elif self.hash:
            return self.hash

    def get_uri(self):
        uri = [];
        query_string = self.get_query_string()
        hash_string = self.get_hash_string()

        if self.protocol:
            uri.append(self.protocol + '://')
        elif self.hostname:
            uri.append('//')

        uri.append(self.hostname)
        uri.append(self.path)
        uri.append('?' + query_string if len(query_string) else '')

        if hash_string:
            uri.append('#' + hash_string)

        return ''.join(uri)

    def get_segment(self, i):
        return self.path.split('/')[i]

    def set_segment(self, i, value):
        split = self.path.split('/')
        split[i] = value
        self.path = '/'.join(split)
        return self

    __getitem__ = get_segment
    __setitem__ = set_segment

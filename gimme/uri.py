from urlparse import parse_qs
import re
import urllib


class QueryString(object):
    _reserved_attrs = ('_query_string', '_parsed')

    def __init__(self, query_string):
        self._query_string = query_string
        self._parsed = parse_qs(query_string)

    def __repr__(self):
        return 'QueryString(%s)' % self._parsed

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, key):
        if key not in QueryString._reserved_attrs:
            try:
                value = self._parsed[key]
            except KeyError, e:
                raise AttributeError(key)
            return value if len(value) > 1 else value[0]
        else:
            return object.__getattr__(self, key)

    def __setattr__(self, key, value):
        if key not in QueryString._reserved_attrs:
            if key not in self._parsed:
                self._parsed[key] = []
            self._parsed[key].append(value)
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
    
    def iteritems(self):
        for i in self:
            yield (i, self[i])


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
        self.request_uri = match.group(4)
        self.query_string = match.group(5)
        self.hash = match.group(6)

        self.query_params = self._parse_query_string(self.query_string) or {}
        self.hash_params = self._parse_query_string(self.hash) or {}

    def _combine_params(self, params):
        result = []

        for k, value in params.iteritems():
            key = self.encode_string(k)
            if value is None:
                result.append(key)
            else:
                result.append(key + '=' + self.encode_string(value))

        return '&'.join(result)

    def _parse_query_string(self, query_string):
        result = {}
        params = query_string.split('&')

        for i in params:
            temp = i.split('=', 1)
            key = self.decode_string(temp[0])
            if len(temp) == 1:
                result[key] = None
            else:
                result[key] = self.decode_string(temp[1])

        return result

    def get_query_string(self):
        return self._combine_params(self.query_params)

    def encode_string(self, s):
        return urllib.quote(s) if self._escape_plus else urllib.quote_plus(s)

    def decode_string(self, s):
        return (urllib.unquote(s) if self._escape_plus else
            urllib.unquote_plus(s))

    def get_hash_string(self):
        if self.hash or self.hash_params:
            return (self.hash if not self.hash_params else
                self._combine_params(self.hash_params))

    def get_uri(self):
        uri = [];
        query_string = self.get_query_string()
        hash_string = self.get_hash_string()

        if self.protocol:
            uri.append(self.protocol + '://')
        elif self.hostname:
            uri.append('//')

        uri.append(self.hostname)
        uri.append(self.request_uri)
        uri.append('?' + query_string if len(query_string) else '')

        if hash_string:
            uri.append('#' + hash_string)

        return ''.join(uri)

    def get_segment(self, i):
        return self.request_uri.split('/')[i]

    def set_segment(self, i, value):
        split = self.request_uri.split('/')
        split[i] = value
        self.request_uri = '/'.join(split)
        return self

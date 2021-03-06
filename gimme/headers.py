from .dotdict import DotDict


class Header(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return "%s: %s" % (self.key, self.value)

    def __repr__(self):
        return "<Header(%s)>" % str(self)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        else:
            return self is other


class HeadersDict(object):
    def __init__(self, initial_data=None):
        self._headers = []

        if initial_data:
            self.update(initial_data)

    def __setitem__(self, key, value):
        self._set_header(key, value)

    def __getitem__(self, key):
        header = self._get_header(key)
        if not header:
            raise KeyError(key)
        return header

    def __delitem__(self, key):
        self._headers.remove(self[key])

    def __contains__(self, key):
        return bool(self._get_header(key))

    def __len__(self):
        return len(self._headers)

    def __repr__(self):
        temp = {}
        for i in self._headers:
            temp[i.key] = i.value
        return repr(temp)

    def __str__(self):
        return self.render()

    def __iter__(self):
        for i in self._headers:
            yield i

    def __eq__(self, other):
        for i in xrange(len(self)):
            try:
                if self._headers[i] != other._headers[i]:
                    return False
            except IndexError:
                return False
        return True

    def _set_header(self, key, value):
        header = self._get_header(key)
        if not header:
            header = Header(key, value)
            self._headers.append(header)
        else:
            header.value = value
        return self

    def _get_header(self, key):
        for header in self._headers:
            if header.key == key:
                return header
        return None

    def keys(self):
        keys = [i.key for i in self._headers]
        return list(set(keys))

    def values(self):
        return [i.value for i in self._headers]

    def items(self):
        return [(i.key, i.value) for i in self._headers]

    def items_str(self):
        return [(str(i.key), str(i.value)) for i in self._headers]

    def iteritems(self):
        for i in self._headers:
            yield (i.key, i.value)

    def update(self, data):
        for key, value in data.iteritems():
            self[key] = value

    def add_header(self, header):
        self._headers.append(header)

    def del_header(self, header):
        self._headers.remove(header)

    def render(self):
        return '\r\n'.join(map(str, self._headers)) + '\r\n\r\n'

    def copy(self):
        copy = HeadersDict()
        copy._headers = list(self._headers)
        return copy

    def clear(self):
        del(self._headers[:])

    def get(self, key, default=None):
        return self[key] if key in self else default

    def get_all(self, key):
        headers = []
        for i in self:
            if i.key == key:
                headers.append(i)
        return headers


class RequestHeaders(DotDict):
    pass


class ResponseHeaders(HeadersDict):
    pass

import types


class OutputBody(object):
    def __init__(self, response, body, chunk_size=4096):
        self.response = response
        self.body = body
        self.chunk_size = chunk_size

    @property
    def body_iterable(self):
        return hasattr(self.body, '__iter__') or (
            isinstance(self.body, types.GeneratorType))

    def __iter__(self):
        if self.body_iterable:
            return self.body
        elif isinstance(self.body, basestring):
            return self._make_iter()
        else:
            return self._make_iter(True)

    def _make_iter(self, convert_to_string=False):
        data = self.body if not convert_to_string else unicode(self.body,
            self.response.charset, 'ignore')
        chunk = data[0:self.chunk_size]
        while chunk:
            if convert_to_string:
                yield chunk.encode(self.response.charset, 'ignore')
            else:
                yield chunk
            data = data[self.chunk_size:]
            chunk = data[0:self.chunk_size]
        raise StopIteration

    def __repr__(self):
        return "<OutputBody()>"

    def __str__(self):
        return ''.join(list(self))

    def __unicode__(self):
        result = []
        for i in self:
            if not isinstance(i, unicode):
                result.append(unicode(i, self.response.charset, 'ignore'))
            else:
                result.append(i)
        return u''.join(result)

    def set(self, data):
        self.body = data

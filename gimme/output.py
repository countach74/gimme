import types


class OutputBody(object):
    def __init__(self, body, chunk_size=4096):
        self.body = body
        self.chunk_size = chunk_size

    @property
    def body_iterable(self):
        return hasattr(self.body, '__iter') or (
            isinstance(self.body, types.GeneratorType))

    def __iter__(self):
        if self.body_iterable:
            return self.body
        elif isinstance(self.body, basestring):
            return self._make_iter()
        else:
            return self._make_iter(True)

    def _make_iter(self, convert_to_string=False):
        pos = 0
        data = self.body if not convert_to_string else str(self.body)
        chunk = data[pos:self.chunk_size]
        while chunk:
            yield chunk
            pos += self.chunk_size
            chunk = data[pos:self.chunk_size]
        raise StopIteration

    def __repr__(self):
        return "<OutputBody()>"

    def __str__(self):
        return ''.join(list(self))

    def set(self, data):
        self.body = data

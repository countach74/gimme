class Encoding(object):
    pass


class Chunked(Encoding):
    def __init__(self, connection, body):
        self.connection = connection
        self.body = body
        self.connection.headers.append(('Transfer-Encoding', 'chunked'))

    def __iter__(self):
        for i in self.body:
            yield '%0x\r\n%s\r\n' % (len(i), i)
        yield '0\r\n\r\n'

    def __repr__(self):
        return "<Chunked()>"

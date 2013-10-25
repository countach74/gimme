from gimme import headers
import unittest


class HeaderTest(unittest.TestCase):
    def setUp(self):
        self.header = headers.Header('Content-Type', 'application/json')

    def test_eq(self):
        assert self.header == 'application/json'
        assert self.header == self.header

    def test_str(self):
        assert str(self.header) == 'Content-Type: application/json'


class HeadersTest(unittest.TestCase):
    def setUp(self):
        self.headers = headers.HeadersDict({
            'Content-Type': 'application/pdf',
            'Content-Length': '2280'
        })

    def test_getitem(self):
        assert self.headers['Content-Type'] == 'application/pdf'

    def test_contains(self):
        assert 'Content-Type' in self.headers
        assert 'Not-Here' not in self.headers

    def test_setitem(self):
        self.headers['Content-Encoding'] = 'chunked'
        assert self.headers['Content-Encoding'] == 'chunked'

    def test_delitem(self):
        del(self.headers['Content-Type'])
        assert not self.headers.get('Content-Type')

    def test_render(self):
        assert self.headers.render() == '\r\n'.join([
            'Content-Length: 2280',
            'Content-Type: application/pdf',
            '\r\n'
        ])

    def test_copy_and_eq(self):
        copy = self.headers.copy()
        assert id(copy) != id(self.headers)
        assert copy == self.headers

    def test_len(self):
        assert len(self.headers) == 2

    def test_clear(self):
        self.headers.clear()
        assert len(self.headers) == 0

    def test_get_all_and_add_header(self):
        new_header = headers.Header('Content-Type', 'text/html')
        self.headers.add_header(new_header)
        the_headers = self.headers.get_all('Content-Type')
        assert len(the_headers) == 2
        assert the_headers[1] is new_header

    def test_get(self):
        assert self.headers.get('Content-Type') == 'application/pdf'
        assert self.headers.get('Content-Encoding', False) is False

    def test_del_header(self):
        new_header = headers.Header('Content-Encoding', 'chunked')
        self.headers.add_header(new_header)
        assert self.headers.get('Content-Encoding') == 'chunked'
        self.headers.del_header(new_header)
        with self.assertRaises(KeyError):
            test_thing = self.headers['Content-Encoding']

    def test_keys(self):
        assert len(self.headers.keys()) == 2

    def test_values(self):
        assert len(self.headers.values()) == 2

    def test_items(self):
        assert len(self.headers.items()) == 2

    def test_iteritems(self):
        assert len(list(self.headers.iteritems())) == 2

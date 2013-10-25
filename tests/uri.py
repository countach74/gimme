import gimme.uri
import unittest


class QueryStringTest(unittest.TestCase):
    def setUp(self):
        self.raw = 'name=bob&item=first_item&item=second_item'
        self.qs = gimme.uri.QueryString(self.raw)

    def test_raw(self):
        assert self.raw == self.qs._query_string

    def test_getattr(self):
        assert self.qs.name == 'bob'
        assert len(self.qs.item) == 2
        assert type(self.qs.item) == list
        assert self.qs.item[0] == 'first_item'

    def test_setattr(self):
        self.qs.some_attr = 'test'
        assert self.qs.some_attr == 'test'

    def test_str(self):
        assert str(self.qs) == self.raw

    def test_getitem(self):
        assert self.qs['name'] == 'bob'

    def test_setitem(self):
        self.qs['something'] = 'another test'
        assert self.qs['something'] == 'another test'

    def test_delitem(self):
        del(self.qs['name'])
        with self.assertRaises(KeyError):
            some_item = self.qs['name']

    def test_contains(self):
        assert 'name' in self.qs
        assert 'not_here' not in self.qs

import gimme.uri
import unittest
import re


class QueryStringTest(unittest.TestCase):
    def setUp(self):
        self.raw = 'name=bob&item=first_item&item=second_item'
        self.qs = gimme.uri.QueryString(self.raw)

    def test_raw(self):
        assert self.raw == self.qs._query_string

    def test_getattr(self):
        assert self.qs.name == 'bob'
        assert len(self.qs.item) == 2
        assert type(self.qs.item) == gimme.uri.QueryValue
        assert self.qs.item[0] == 'first_item'

    def test_setattr(self):
        self.qs.some_attr = 'test'
        assert self.qs.some_attr == 'test'

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

    def test_iadd(self):
        self.qs.item += 'third_item'
        assert 'third_item' in self.qs.item

    def test_isub(self):
        self.qs.item -= 'second_item'
        assert 'second_item' not in self.qs.item

    def test_add(self):
        val = self.qs.item + 'test'
        assert 'test' in val

    def test_sub(self):
        val = self.qs.item - 'second_item'
        assert 'second_item' not in val


def make_uri_test(name, uri_before, params):
    class URITest(unittest.TestCase):
        def setUp(self):
            self.uri = gimme.uri.URI(uri_before)

        def test_get_segment(self):
            if 'get_segment' in params:
                assert self.uri.get_segment(params['get_segment']) == (
                    params['get_segment_value'])

        def test_set_segment(self):
            if 'set_segment' in params:
                self.uri.set_segment(params['set_segment'],
                    params['set_segment_value'])
                assert self.uri.get_segment(params['set_segment']) == (
                    params['set_segment_value'])

        def test_protocol(self):
            if 'protocol' in params:
                assert self.uri.protocol == params['protocol']

        def test_hostname(self):
            if 'hostname' in params:
                assert self.uri.hostname == params['hostname']

        def test_path(self):
            if 'request_uri' in params:
                assert self.uri.path == params['request_uri']

        def test_query_string(self):
            if 'query_string' in params:
                assert self.uri.query_string == params['query_string']

        def test_hash(self):
            if 'hash' in params:
                assert self.uri.hash == params['hash']

        def test_query_params(self):
            if 'query_params' in params:
                for k, v in params['query_params'].iteritems():
                    assert (k in self.uri.query_params and
                        self.uri.query_params[k] == v)

        def test_hash_params(self):
            if 'hash_params' in params:
                for k, v in params['hash_params'].iteritems():
                    assert (k in self.uri.hash_params and
                        self.uri.hash_params[k] == v)

    URITest.__name__ = name
    return URITest


URITest1 = make_uri_test('URITest1', 'http://www.google.com', {
    'protocol': 'http',
    'hostname': 'www.google.com',
    'request_uri': '',
    'query_string': '',
    'get_query_string': '',
    'hash': '',
    'get_hash_string': '',
    'query_params': {},
    'hash_params': {},
})

URITest2 = make_uri_test('URITest2', 'https://www.thirteen8.com/something/cool?param1=value1&param2=value2#hash=hash_value', {
    'protocol': 'https',
    'hostname': 'www.thirteen8.com',
    'request_uri': '/something/cool',
    'query_string': 'param1=value1&param2=value2',
    'hash': 'hash=hash_value',
    'query_params': {'param1': 'value1', 'param2': 'value2'},
    'hash_params': {'hash': 'hash_value'},
})

URITest3 = make_uri_test('URITest3', '/slot1/slot2?param1=value1#hash=hash_value', {
    'request_uri': '/slot1/slot2',
    'query_string': 'param1=value1',
    'hash': 'hash=hash_value',
    'get_segment': 1,
    'get_segment_value': 'slot1',
    'set_segment': 2,
    'set_segment_value': 'a_new_value'
})

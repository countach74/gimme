import gimme.dotdict
import unittest


class DotDictTest(unittest.TestCase):
    def setUp(self):
        self.dd = gimme.dotdict.DotDict({
            'key': 'value',
            'name': 'bob'
        })

    def test_getattr(self):
        assert self.dd.key == 'value'

    def test_setattr(self):
        self.dd.set_test = 'data'
        assert self.dd.set_test == 'data'

    def test_nested(self):
        self.dd.nested_test = {
            'some_key': {
                'another_key': 'value'
            }
        }
        assert self.dd.nested_test.some_key.another_key == 'value'

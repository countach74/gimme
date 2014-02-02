from gimme.parsers.contenttype import ContentType
import unittest


class ContentTypeTest(unittest.TestCase):
    def setUp(self):
        self.ct1 = ContentType('application/json')
        self.ct2 = ContentType('html')
        self.ct3 = ContentType('text/*')

    def test_eq(self):
        # Test ct1 passes
        assert self.ct1 == 'application/json'
        assert self.ct1 == 'application/*'
        assert self.ct1 == 'json'

        # Test ct2 passes
        assert self.ct2 == 'text/html'
        assert self.ct2 == 'html'

        # Test ct3 passes
        assert self.ct3 == 'text/*'
        assert self.ct3 == 'text/html'

        # Test ct1 fails
        assert self.ct1 != 'application/bob'
        assert self.ct1 != 'text/html'
        assert self.ct1 != 'html'

        # Test ct2 fails
        assert self.ct2 != 'json'

        # Test ct3 fails
        assert self.ct3 != 'application/*'

    def test_ne(self):
        # Test ct1 passes
        assert not self.ct1 != 'application/json'
        assert not self.ct1 != 'application/*'
        assert not self.ct1 != 'json'

        # Test ct2 passes
        assert not self.ct2 != 'text/html'
        assert not self.ct2 != 'html'

        # Test ct3 passes
        assert not self.ct3 != 'text/*'
        assert not self.ct3 != 'text/html'

        # Test ct1 fails
        assert not self.ct1 == 'application/bob'
        assert not self.ct1 == 'text/html'
        assert not self.ct1 == 'html'

        # Test ct2 fails
        assert not self.ct2 == 'json'

        # Test ct3 fails
        assert not self.ct3 == 'application/*'

    def test_str(self):
        assert str(self.ct1) == 'application/json'
        assert str(self.ct2) == 'html'
        assert str(self.ct3) == 'text/*'

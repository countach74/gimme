import unittest
from . import test_helpers
from gimme.app import App
from gimme.request import Request


class RequestTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.app = App()
        body = '{"test": "data"}'
        self.environ = test_helpers.make_environ(
            uri='http://www.google.com/somewhere/something?this=is+awesome',
            body=body, method='POST')
        self.environ['HTTP_CONTENT_TYPE'] = 'application/json'
        self.environ['HTTP_CONTENT_LENGTH'] = str(len(body))
        self.environ['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.request = Request(self.app, self.environ)

    def setUp(self):
        pass

    def test_type(self):
        # Test fails
        assert self.request.type != 'crash'
        assert self.request.type != 'text/*'
        assert self.request.type != 'text/html'

        # Test passes
        assert self.request.type == 'json'
        assert self.request.type == 'application/*'
        assert self.request.type == 'application/json'

    def test_body(self):
        assert self.request.raw_body == '{"test": "data"}'

    def test_get(self):
        assert self.request.get('content_type') == 'application/json'

    def test_accepts(self):
        assert self.request.accepts('text/html')

    def test_param(self):
        # Not quite sure how I should test this yet
        pass

    def test_query(self):
        assert self.request.query.this == 'is awesome'
        assert 'crap' not in self.request.query

    def test_xhr(self):
        assert self.request.xhr

    def test_path(self):
        assert self.request.path == '/somewhere/something'

    def test_host(self):
        assert self.request.host == 'www.google.com'

    def test_subdomains(self):
        assert self.request.subdomains == ['www']

    def test_ip(self):
        assert self.request.ip == '127.0.0.1'

    def test_secure(self):
        assert self.request.secure == False

    def test_original_url(self):
        assert self.request.original_url == '/somewhere/something?this=is%20awesome'

    def test_protocol(self):
        assert self.request.protocol == 'HTTP/1.1'

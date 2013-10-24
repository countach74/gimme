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
            body=body, method='POST')
        self.environ['HTTP_CONTENT_TYPE'] = 'application/json'
        self.environ['HTTP_CONTENT_LENGTH'] = str(len(body))
        self.environ['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.request = Request(self.app, self.environ)

    def setUp(self):
        pass

    def test_is_type(self):
        # Test fails
        assert self.request.is_type('crash') is False
        assert self.request.is_type('text/*') is False
        assert self.request.is_type('text/html') is False

        # Test passes
        assert self.request.is_type('json') is True
        assert self.request.is_type('application/*') is True
        assert self.request.is_type('application/json') is True

    def test_body(self):
        assert self.request.raw_body == '{"test": "data"}'

    def test_get(self):
        assert self.request.get('content_type') == 'application/json'

    def test_accepts(self):
        assert self.request.accepts('text/html')

    def test_param(self):
        # Not quite sure how I should test this yet
        pass

    def test_xhr(self):
        assert self.request.xhr

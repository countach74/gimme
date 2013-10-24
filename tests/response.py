import unittest
import gimme
import datetime
from . import test_helpers


class ResponseTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.app = gimme.App()
        body = '{"test": "data"}'
        self.environ = test_helpers.make_environ(
            body=body, method='POST')
        self.environ['HTTP_CONTENT_TYPE'] = 'application/json'
        self.environ['HTTP_CONTENT_LENGTH'] = str(len(body))
        self.environ['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        
        class TestController(gimme.Controller):
            def endpoint1(self):
                return 'endpoint1_response'

        self.controller = TestController
        self.app.routes.post('/', self.controller.endpoint1)

        self.request, self.response = self.app.routes.match(self.environ)

    def test_set_get(self):
        self.response.set('Content-Type', 'text/plain')
        assert self.response.get('Content-Type') == 'text/plain'

    def test_location(self):
        self.response.redirect('/somewhere_else')
        assert self.response.status_code == 302
        assert self.response.get('Location') == '/somewhere_else'

    def test_type(self):
        self.response.type('application/pdf')
        assert self.response.headers['Content-Type'] == 'application/pdf'

    def test_cookie(self):
        self.response.cookie('simple_cookie', 'some_data')
        assert self.response.headers['Set-Cookie'] == 'simple_cookie=some_data; Path=/'

        self.response.cookie('complex_cookie', 'more_data', path='/somewhere',
            domain='something.test.com', expires=360000)
        # Add assert to test cookie

    def test_status(self):
        self.response.status(401)
        assert self.response.status_code == 401
        assert self.response.status_message == 'Not Authorized'

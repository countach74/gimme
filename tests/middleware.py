import gimme
import unittest
import zlib
from .test_helpers import make_environ


class MiddlewareTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

        self.app = gimme.App()

        class TestController(gimme.Controller):
            def endpoint1(self):
                return 'endpoint1_response'

            def endpoint2(self):
                return {'test': 'data'}

            def endpoint3(self):
                return self.request.body

        self.app.routes.get('/endpoint1', TestController.endpoint1)
        self.app.routes.get('/endpoint2', TestController.endpoint2)
        self.app.routes.post('/endpoint3', TestController.endpoint3)

    def start_response(self, status, headers):
        self.status = status
        self.headers = headers

    @staticmethod
    def endpoint1(self):
        pass

    @staticmethod
    def endpoint2(self):
        pass


class CookieParserTest(MiddlewareTest):
    def setUp(self):
        self.app.use(gimme.middleware.cookie_parser())
        self.environ = make_environ('GET', '/endpoint1')

    def test_cookie_parser(self):
        request, response = self.app.routes.match(self.environ)
        response._render()
        assert hasattr(request, 'cookies')
        assert 'gimme_session' in request.cookies
        assert request.cookies.gimme_session == (
            'f6225d448db99e2102cc25ef9c1d123d71f132ba3705fc168bd72a717cb9638b')


class SessionTest(MiddlewareTest):
    def setUp(self):
        self.app.use(gimme.middleware.cookie_parser())
        self.app.use(gimme.middleware.session())
        self.environ = make_environ('GET', '/endpoint1')

    def test_session(self):
        request, response = self.app.routes.match(self.environ)
        response._render()
        request.session['test'] = 'zomg that is cool'
        assert request.session['test'] == 'zomg that is cool'


class JsonTest(MiddlewareTest):
    def setUp(self):
        self.app.use(gimme.middleware.json())
        self.environ = make_environ('POST', '/endpoint3', None,
            '{"simple": "json test"}')
        self.environ['HTTP_CONTENT_TYPE'] = 'application/json'

    def test_json(self):
        request, response = self.app.routes.match(self.environ)
        response._render()
        assert 'simple' in request.body
        assert request.body.simple == 'json test'


class UrlEncodedTest(MiddlewareTest):
    def setUp(self):
        self.app.use(gimme.middleware.urlencoded())
        self.environ = make_environ('POST', '/endpoint3', None,
            'some_test=that+is+cool')
        self.environ['HTTP_CONTENT_TYPE'] = 'application/x-www-form-urlencoded'

    def test_urlencoded(self):
        request, response = self.app.routes.match(self.environ)
        response._render()
        assert 'some_test' in request.body
        assert request.body.some_test == 'that is cool'


class CompressTest(MiddlewareTest):
    def setUp(self):
        self.app.use(gimme.middleware.compress())
        self.environ = make_environ('GET', '/endpoint1')

    def test_compress(self):
        request, response = self.app.routes.match(self.environ)
        response._render()
        should_be = zlib.compress('endpoint1_response')
        assert should_be == response.body

    def test_not_accepted(self):
        del(self.environ['HTTP_ACCEPT_ENCODING'])
        request, response = self.app.routes.match(self.environ)
        response._render()
        assert response.body == 'endpoint1_response'

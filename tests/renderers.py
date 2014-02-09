import unittest
import zlib
from jinja2 import Environment, DictLoader
import gimme
from gimme.engines import Jinja2Engine
from gimme.renderers import (
    BaseRenderer,
    BulkRenderer, 
    Format,
    Template,
    Json,
    Compress
)


class RendererSetUp(object):
    def setUp(self):
        class TestController(gimme.Controller):
            def index(self):
                return {'this': 'is test data.'}

        self.TestController = TestController
        self.engine = Jinja2Engine(environment=
            Environment(loader=DictLoader({
                'index.html': 'this is a test. {{this}}'
            }))
        )
        self.app = gimme.App(engine=self.engine)
        self.app.routes.get('/', TestController.index)
        self.request, self.response = self.app.routes.match({
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET',
            'HTTP_ACCEPT_ENCODING': 'deflate'
        })
        self.controller = TestController(self.app, self.request, self.response)


class BaseRendererTest(unittest.TestCase):
    def test_eq(self):
        renderer = BaseRenderer()
        format_ = renderer == 'text/html'
        assert isinstance(format_, Format)


class TemplateTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        renderer = Template('index.html')
        assert renderer.render(self.controller,
            self.controller.index()) == 'this is a test. is test data.'


class JsonTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        renderer = Json()
        assert renderer.render(self.controller,
            self.controller.index() == '{"this": "is test data."}')
        assert self.response.type == 'application/json'


class CompressTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        renderer = Compress()
        compressed_data = zlib.compress("{'this': 'is test data.'}")
        assert renderer.render(self.controller,
            str(self.controller.index())) == compressed_data
        assert self.response.headers['Content-Encoding'] == 'deflate'


class FormatTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        html_renderer = Format(Template('index.html'), 'text/html')
        json_renderer = Format(Json(), 'application/json')

        html_request, html_response = self.app.routes.match({
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET',
            'HTTP_ACCEPT': 'text/html'
        })

        json_request, json_response = self.app.routes.match({
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET',
            'HTTP_ACCEPT': 'application/json'
        })

        html_controller = self.TestController(self.app, html_request,
            html_response)

        json_controller = self.TestController(self.app, json_request,
            json_response)

        assert html_renderer.render(
            html_controller, html_controller.index()) == (
            'this is a test. is test data.')

        assert json_renderer.render(
            json_controller, json_controller.index()) == (
            '{"this": "is test data."}')

        assert html_response.type == 'text/html; charset=UTF-8'
        assert json_response.type == 'application/json'

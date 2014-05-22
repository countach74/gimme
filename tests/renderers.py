import unittest
import zlib
import json
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
            def index(self, request, response):
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
        self.controller = TestController(self.app)


class BaseRendererTest(unittest.TestCase):
    def test_eq(self):
        renderer = BaseRenderer()
        format_ = renderer == 'text/html'
        assert isinstance(format_, Format)


class TemplateTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        renderer = Template('index.html')
        assert renderer.render(self.controller,
            self.controller.index(self.request, self.response), self.request,
            self.response) == 'this is a test. is test data.'


class JsonTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        renderer = Json()
        assert renderer.render(self.controller,
            self.controller.index(self.request, self.response),
            self.request, self.response) == '{"this": "is test data."}'
        assert self.response.type == 'application/json'


class CompressTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        renderer = Compress()
        compressed_data = zlib.compress("{'this': 'is test data.'}")
        assert renderer.render(self.controller,
            str(self.controller.index(self.request, self.response)),
            self.request, self.response) == compressed_data
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

        html_controller = self.TestController(self.app)
        json_controller = self.TestController(self.app)

        assert html_renderer.render(
            html_controller, html_controller.index(html_request, html_response),
            html_request, html_response) == (
            'this is a test. is test data.')

        assert json_renderer.render(
            json_controller, json_controller.index(json_request, json_response),
            json_request, json_response) == (
            '{"this": "is test data."}')

        assert html_response.type == 'text/html; charset=UTF-8'
        assert json_response.type == 'application/json'


class BulkRendererTest(RendererSetUp, unittest.TestCase):
    def test_render(self):
        renderer = BulkRenderer([Json(), Compress()])
        compressed = zlib.compress(json.dumps(self.controller.index(
            self.request, self.response)))

        assert renderer.render(self.controller,
            self.controller.index(self.request, self.response),
            self.request, self.response) == compressed
        assert self.response.type == 'application/json'
        assert self.response.headers['Content-Encoding'] == 'deflate'

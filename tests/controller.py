import unittest
import gimme
from gimme.controller import Controller, ControllerMethod, MethodRenderer
from gimme.engines import Jinja2Engine
from gimme.renderers import Format, BulkRenderer, Template, Json
from test_helpers import make_environ
from jinja2 import Environment, DictLoader


class ControllerTest(unittest.TestCase):
    def setUp(self):
        class TestController(Controller):
            def string(self):
                return "Awesome!"

            def dictionary(self):
                return {"this": "is a dictionary"}

        self.TestController = TestController
        self.environment = Environment(loader=DictLoader({
            'test.html': "ZOMG, this is a test! this = {{this}}"
        }))
        self.app = gimme.App(engine=Jinja2Engine(environment=self.environment))
        self.app.routes.get('/string', TestController.string)
        self.app.routes.get('/dictionary', TestController.dictionary.json())

    def get_request_response(self, *args, **kwargs):
        return self.app.routes.match(make_environ(*args, **kwargs))

    def instantiate_controller(self, request, response):
        return self.TestController(self.app, request, response)

    def test_controller_method_creation(self):
        assert isinstance(self.TestController.string, ControllerMethod)

    def test_method_renderer_creation(self):
        method_renderer = self.TestController.dictionary + 'something.html'
        assert isinstance(method_renderer, MethodRenderer)

    def test_json(self):
        controller = self.instantiate_controller(
            *self.get_request_response('/dictionary'))
        json = self.TestController.dictionary.json()
        assert json() == '{"this": "is a dictionary"}'
        assert isinstance(json, MethodRenderer)

    def test_format_creation(self):
        '''
        This should be split into several tests and really doesn't belong in
        this test case.
        '''
        controller = self.instantiate_controller(
            *self.get_request_response('/dictionary'))

        template = Template('test.html') == 'text/html'
        json = Json() == 'application/json'

        method_renderer = self.TestController.dictionary + (
            template | json
        )

        assert isinstance(template, Format)
        assert isinstance(json, Format)
        assert isinstance(method_renderer, MethodRenderer)
        assert template.render(controller, {'this': 'things'}) == (
            'ZOMG, this is a test! this = things')
        assert json.render(controller, {'this': 'things'}) == (
            '{"this": "things"}')

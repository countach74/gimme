import unittest
import gimme
from gimme.controller import Controller, ControllerMethod, MethodRenderer
from gimme.engines import Jinja2Engine
from gimme.renderers import Format, BulkRenderer, Template, Json, Compress
from test_helpers import make_environ
from jinja2 import Environment, DictLoader


class ControllerSetUp(object):
    def setUp(self):
        class TestController(Controller):
            def index(self):
                return {'this': 'is test data'}

        self.engine = Jinja2Engine(environment=
            Environment(loader=DictLoader({
                'index.html': 'this is a test. {{this}}'
            }))
        )
        self.app = gimme.App(engine=self.engine)
        self.TestController = TestController


class ControllerTest(ControllerSetUp, unittest.TestCase):
    def test_meta_modifications(self):
        assert isinstance(self.TestController.index, ControllerMethod)


class ControllerMethodTest(ControllerSetUp, unittest.TestCase):
    def test_add(self):
        json_renderer = self.TestController.index + Json()
        template_renderer = self.TestController.index + Template('something')
        string_renderer = self.TestController.index + 'something'

        assert isinstance(json_renderer, MethodRenderer)
        assert isinstance(template_renderer, MethodRenderer)
        assert isinstance(string_renderer, MethodRenderer)

    def test_template(self):
        assert isinstance(self.TestController.index.json(), MethodRenderer)
        assert isinstance(self.TestController.index.template('something'),
            MethodRenderer)
        assert isinstance(self.TestController.index.compress(), MethodRenderer)

    def test_eq(self):
        format_ = self.TestController.index == 'text/html'
        assert isinstance(format_, Format)

    def test_call(self):
        instantiated_controller = self.TestController(None, None, None)
        result = self.TestController.index()
        assert result['this'] == 'is test data'


class MethodRendererTest(ControllerSetUp, unittest.TestCase):
    def setUp(self):
        ControllerSetUp.setUp(self)

        self.method_renderer = self.TestController.index + 'index.html'

    def check_for_renderer(self, renderer):
        for i in self.method_renderer[1:]:
            if isinstance(i, renderer):
                return True
        return False

    def test_add(self):
        self.method_renderer + Compress()

        assert self.check_for_renderer(Compress), (
            "Compress object did not get added to method_renderer")

    def test_compress(self):
        self.method_renderer.compress()

        assert self.check_for_renderer(Compress), (
            "Compress object did not get added to method_renderer")

    def test_template(self):
        self.method_renderer.template('something')

        assert self.check_for_renderer(Template), (
            "Template object did not get added to method_renderer")

    def test_json(self):
        self.method_renderer.json()

        assert self.check_for_renderer(Json), (
            "Json object did not get added to method_renderer")

    def test_call(self):
        # Need to instantiate the controller before templates can be rendered
        controller = self.TestController(self.app, None, None)
        assert self.method_renderer() == 'this is a test. is test data'

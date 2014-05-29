import gimme
import unittest
from .test_helpers import make_environ


class RoutesTest(unittest.TestCase):
  def setUp(self):
    self.app = gimme.App()

    class TestController(gimme.Controller):
        def endpoint1(self):
            return 'endpoint1_response'

    self.controller = TestController

  def test_query_string(self):
    self.app.routes.get('/', self.controller.endpoint1) 

    request, response, route = self.app.routes.match(make_environ(
        uri='/?id=3'))

    self.assertEqual(request.query.id, '3')

  def test_param(self):
    self.app.routes.get('/user/:id', self.controller.endpoint1)
    
    request, response, route = self.app.routes.match(make_environ(
        uri='/user/4'))

    self.assertEqual(request.params.id, '4')

  def test_optional_param(self):
    self.app.routes.get('/user/:id/:message?', self.controller.endpoint1)

    request, response, route = self.app.routes.match(make_environ(
        uri='/user/3/4'))

    request2, response2, route2 = self.app.routes.match(make_environ(
        uri='/user/3'))

    self.assertEqual(request.params.id, '3')
    self.assertTrue(bool(request2))

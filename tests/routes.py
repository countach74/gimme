import gimme
import unittest
import re
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


class RouteTest(unittest.TestCase):
  def setUp(self):
    self.route = gimme.routes.Route('/user/:id')

  def test_reverse(self):
    assert self.route.reverse({'id': 3}) == '/user/3'
    with self.assertRaises(KeyError):
      self.route.reverse({})

  def test_match(self):
    assert self.route.match('/user/3')
    assert self.route.match('/user/3/')
    assert not self.route.match('/')

    route = gimme.routes.Route('/')
    assert route.match('/')
    assert not route.match('//')
    assert not route.match('/user')

  def test_name(self):
    self.route._routes = gimme.routes.Routes(None)
    named = self.route.name('bob')
    assert self.route._name == 'bob'
    assert named == self.route

  def test_name_fail(self):
    with self.assertRaises(TypeError):
      self.route.name('bob')


class RegexRouteTest(unittest.TestCase):
  def setUp(self):
    self.route = gimme.routes.Route(re.compile('/bob/(?P<id>[0-9]+)/?'))

  def test_match(self):
    assert self.route.match('/bob/3')
    assert self.route.match('/bob/3/')
    assert not self.route.match('/bob')

  def test_reverse(self):
    assert self.route.reverse({'id': 4}) == '/bob/4'

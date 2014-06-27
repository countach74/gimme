import gimme
import unittest
import re
from .test_helpers import make_environ


class RoutesTest(unittest.TestCase):
  def setUp(self):
    self.app = gimme.App()
    self.routes = self.app.routes
    self.route = self.routes.get('/', None)

  def test_get(self):
    assert isinstance(self.route, gimme.routes.Route)

  def test_match(self):
    assert self.routes.match({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'})
    assert self.routes.match({'REQUEST_METHOD': 'POST', 'PATH_INFO': '/'})[1].status == 404

  def test_get_route_by_name(self):
    self.route.name('root')
    assert self.routes.get_route_by_name('root') == self.route


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

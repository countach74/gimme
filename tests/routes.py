from gimme.app import App
import unittest


class TestRoutes(unittest.TestCase):
  def setUp(self):
    self.app = App()

    def endpoint():
      return 'cool'

    self.endpoint = endpoint

  def test_query_string(self):
    self.app.routes.get('/', self.endpoint) 

    request = self.app.routes.match({
      'REQUEST_METHOD': 'GET',
      'PATH_INFO': '/',
      'QUERY_STRING': 'id=3'
    })

    self.assertEqual(request.query.id, '3')

  def test_param(self):
    self.app.routes.get('/user/:id', self.endpoint)
    
    request = self.app.routes.match({
      'REQUEST_METHOD': 'GET',
      'PATH_INFO': '/user/4'
    })

    self.assertEqual(request.params.id, '4')

  def test_optional_param(self):
    self.app.routes.get('/user/:id/:message?', self.endpoint)

    request = self.app.routes.match({
      'REQUEST_METHOD': 'GET',
      'PATH_INFO': '/user/3/4'
    })

    request2 = self.app.routes.match({
      'REQUEST_METHOD': 'GET',
      'PATH_INFO': '/user/3'
    })

    self.assertEqual(request.params.id, '3')
    self.assertTrue(bool(request2))

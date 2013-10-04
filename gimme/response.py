from .headers import ResponseHeaders


class Response(object):
  def __init__(self, app, route):
    self.app = app
    self.route = route
    self.status = '200 OK'

    try:
      self.headers = ResponseHeaders(dict(app.get('default headers')))
    except KeyError, e:
      self.headers = ResponseHeaders()

    self._controller_class = route.method.im_class
    self._method_name = route.method.__name__
    
  def _prepare(self, method, start_response):
    self.body = method()
    start_response(self.status, self.headers.items())
    
  def set(self, key, value):
    self.headers[key] = value
    
  def get(self, key):
    return self.headers[key]
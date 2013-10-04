from .headers import ResponseHeaders


class Response(object):
  def __init__(self, app, route):
    self.app = app
    self.route = route
    self.controller_class = route.method.im_class
    self.headers = ResponseHeaders(dict(app.get('default headers')))


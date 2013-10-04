from .request import request


class WSGIAdapter(object):
  def __init__(self, app):
    self.app = app

  def process(self, environ, start_response):
    request, response = self.app.routes.match(environ)
    controller = response.controller_class(self.app, request, response)
    method_name = response.route.method.im_func.func_name

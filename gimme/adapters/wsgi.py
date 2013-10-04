class WSGIAdapter(object):
  def __init__(self, app):
    self.app = app

  def process(self, environ, start_response):
    request, response = self.app.routes.match(environ)
    controller = response._controller_class(self.app, request, response)
    method = getattr(controller, response._method_name)
    response._prepare(method, start_response)
    yield str(response.body)
class WSGIAdapter(object):
  def __init__(self, app):
    self.app = app

  def process(self, environ, start_response):
    request = self.app.routes.match(environ)
    if request:
      return request.serve()
    else:
      start_response('404 Not Found', [('Content-Type', 'text/html')])
      yield "Oh no :("

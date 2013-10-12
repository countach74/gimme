import contextlib
from ..response import Response
from ..controller import ErrorController


class WSGIAdapter(object):
  def __init__(self, app):
    self.app = app

  def _get_middleware(self, request, response):
    all_middleware = self.app._middleware + response.route.middleware
    return map(lambda x: x(self.app, request, response), all_middleware)

  def process(self, environ, start_response):
    request, response = self.app.routes.match(environ)
    controller = response._controller_class(self.app, request, response)
    method = getattr(controller, response._method_name)

    all_middleware = self._get_middleware(request, response)

    try:
      with contextlib.nested(*all_middleware):
        response._prepare(method)
    except Exception, e:
      err_response = Response(self.app, self.app.routes.http500)
      err_controller = ErrorController(self.app, request, err_response)

      with contextlib.nested(*all_middleware):
        err_response._prepare(err_controller.http500)

      start_response(err_response._status, err_response.headers.items())
      yield str(err_response.body)
    else:
      start_response(response._status, response.headers.items())
      yield str(response.body)

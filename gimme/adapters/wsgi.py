import contextlib
from ..response import Response
from ..controller import ErrorController


class WSGIAdapter(object):
    def __init__(self, app):
        self.app = app

    def _get_middleware(self, request, response):
        all_middleware = self.app._middleware + response.route.middleware
        return map(lambda x: x(self.app, request, response), all_middleware)

    def _get_app_middleware(self, request, response):
        return map(lambda x: x(self.app, request, response),
            self.app._middleware)

    def process(self, environ, start_response):
        request, response = self.app.routes.match(environ)

        try:
            response._render()
        except Exception, e:
            err_response = Response(self.app, self.app.routes.http500, request)
            err_response._render([])
            start_response(err_response._status, err_response.headers.items())
            yield str(err_response.body)
        else:
            start_response(response._status, response.headers.items())
            yield str(response.body)

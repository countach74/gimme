import contextlib
from .response import Response
from .controller import ErrorController
from .errors import HTTPError


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
            err = e if isinstance(e, HTTPError) else HTTPError(500)
            err_response = err.make_response(request)
            err_response._render([])

            start_response(str(err_response.status), err_response.headers.items_str())
            return err_response.body
        else:
            start_response(str(response.status), response.headers.items_str())
            return response.body

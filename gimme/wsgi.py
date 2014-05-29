import contextlib
from .response import Response
from .controller import ErrorController
from .errors import HTTPError, AbortRender

try:
    from contextlib import nested
except ImportError:
    from .util import nested


class WSGIAdapter(object):
    def __init__(self, app):
        self.app = app

    def _get_middleware(self, request, response):
        all_middleware = self.app.middleware + response.route.middleware
        return map(lambda x: x(self.app, request, response), all_middleware)

    def _get_app_middleware(self, request, response):
        return map(lambda x: x(self.app, request, response),
            self.app.middleware)

    def process(self, environ, start_response):
        request, response, route = self.app.routes.match(environ)

        try:
            self._render(request, response, route)
        except Exception, e:
            if isinstance(e, Response):
                start_response(str(e.status), e.get_headers())
                return e.body
            else:
                err = e if isinstance(e, HTTPError) else HTTPError(500)
                err_response, err_route = err.make_response(self.app)
                self._render(request, err_response, err_route, [])
                start_response(str(err_response.status), err_response.get_headers())
                return err_response.body
        else:
            start_response(str(response.status), response.get_headers())
            return response.body

    def _render(self, request, response, route, middleware=None):
        if middleware is None:
            middleware = self.app.middleware + route.middleware
        elif not middleware:
            middleware = []

        response._instantiated_middleware.extend(self._instantiate_middleware(
            middleware, request, response))

        with nested(*response._instantiated_middleware):
            try:
                if not response._aborted:
                    response.body = route.method(request, response)
            except AbortRender:
                response._aborted = route.method

    def _instantiate_middleware(self, middleware, request, response):
        result = []
        for i in middleware:
            result.append(i(self.app, request, response))
        return result

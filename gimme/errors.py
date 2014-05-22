from . import response
from . import controller
from .parsers.status import StatusCode
import gimme.routes


class GimmeError(Exception):
    pass


class RouteError(GimmeError):
    pass


class TemplateError(GimmeError):
    pass


class AcceptFormatError(GimmeError):
    pass


class FDError(GimmeError):
    pass


class MultipartError(GimmeError):
    pass


class AbortRender(GimmeError):
    pass


class HTTPError(GimmeError):
    def __init__(self, status=500):
        self.status = StatusCode(status)
        try:
            method = getattr(controller.ErrorController, 'http%s'
                % self.status.code)
        except AttributeError:
            method = controller.ErrorController.generic

        self.route = gimme.routes.RouteMapping('*', [], method,
            controller.ErrorController(None))

    def make_response(self, app):
        res = response.Response(app, self.route)
        res.status = self.status.get()
        return res


class HTTPRedirect(HTTPError):
    def __init__(self, url, status=302):
        self.url = url
        HTTPError.__init__(self, status)

    def make_response(self, app):
        res = response.Response(app, self.route)
        res.status = self.status.get()
        res.redirect(self.url, self.status.code)
        return res

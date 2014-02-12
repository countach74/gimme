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

        self.route = gimme.routes.RouteMapping('*', [], method)

    def make_response(self, request):
        res = response.Response(request.app, self.route, request)
        res.status = self.status.get()
        return res


class HTTPRedirect(HTTPError):
    def __init__(self, url, status=301):
        self.url = url
        HTTPError.__init__(self, status)

    def make_response(self, request):
        res = response.Response(request.app, self.route, request)
        res.status = self.status.get()
        res.redirect(self.url, self.status.code)
        return res

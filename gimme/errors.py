from . import response
from . import controller
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


class HTTPError(GimmeError):
    def __init__(self, status=500, message=None):
        self.status = status
        self.message = message or response.Response._status_code_map[status]
        try:
            method = getattr(controller.ErrorController, 'http%s' % status)
        except AttributeError:
            method = controller.ErrorController.generic

        self.route = gimme.routes.Route(None, '*', [], method)

    def make_response(self, request):
        res = response.Response(request.app, self.route, request)
        res.status = '%s %s' % (self.status, self.message)
        return res


class HTTPRedirect(HTTPError):
    def __init__(self, url, status=301):
        self.url = url
        HTTPError.__init__(self, status)

    def make_response(self, request):
        res = response.Response(request.app, self.route, request)
        res.status = '%s %s' % (self.status, self.message)
        res.redirect(self.url, self.status)
        return res

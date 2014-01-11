import sys
import traceback
from .renderers import view


class Controller(object):
    def __init__(self, app, request, response):
        self.app = app
        self.request = request
        self.response = response


class ErrorController(Controller):
    @view('errors/404.html')
    def http404(self):
        self.response.status(404)
        return {
            'headers': self.request.headers,
        }

    @view('errors/500.html')
    def http500(self):
        self.response.status(500)
        e_type, e_value, e_traceback = sys.exc_info()
        traceback.print_exception(e_type, e_value, e_traceback)
        return {
            'headers': self.request.headers,
            'traceback': traceback.format_exception(
                e_type,
                e_value,
                e_traceback)
        }

    @view('errors/generic.html')
    def generic(self):
        return {
            'status': self.response._status
        }

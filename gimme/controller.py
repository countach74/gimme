import sys
import traceback
from jinja2 import Environment, PackageLoader


class Controller(object):
    def __init__(self, app, request, response):
        self.app = app
        self.request = request
        self.response = response


class ErrorController(Controller):
    def __init__(self, *args, **kwargs):
        Controller.__init__(self, *args, **kwargs)
        self.environment = Environment(
            loader=PackageLoader('gimme', 'templates'))

    def http404(self):
        self.response.status = 404

        return self.environment.get_template('errors/404.html').render({
            'headers': self.request.headers,
        })

    def http500(self):
        self.response.status = 500
        e_type, e_value, e_traceback = sys.exc_info()
        traceback.print_exception(e_type, e_value, e_traceback)

        return self.environment.get_template('errors/500.html').render({
            'message': "Oh snap! Something's borked. :(",
            'headers': self.request.headers,
            'traceback': traceback.format_exception(
                e_type,
                e_value,
                e_traceback)
        })

    def generic(self):
        return self.environment.get_template('errors/generic.html').render({
            'status': self.response._status
        })

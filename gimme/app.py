import os
import sys
from .routes import Routes
from .errors import TemplateError
from .wsgi import WSGIAdapter
from .servers.http import HTTPServer
from .servers.logger import SysLogger
from .middleware import connection_helper


class App(object):
    def __init__(self, name='gimme', logger=SysLogger):
        self.logger = logger(name)
        self.routes = Routes(self)
        self.engines = {}

        self._middleware = []
        self.__wsgi = WSGIAdapter(self)
        self.__env_config = {}

        self.dirname = os.path.dirname(os.path.abspath(sys.argv[0]))

        # Dictionary to store defined params
        self.__params = {}

        # Dictionary to store app config
        self.__config = {
            'env': 'development',
            'default headers': {
                'Content-Type': 'text/html; charset=UTF-8',
                'X-PoweredBy': 'Blood, sweat, and tears',
                'X-BadIdea': '; DROP TABLE users;'
            }
        }

    def __call__(self, environ, start_response):
        return self.__wsgi.process(environ, start_response)

    def listen(self, port=8080, host='127.0.0.1', http_server=HTTPServer):
        server = http_server(self, host, port)
        server.start()

    def use(self, middleware):
        self._middleware.append(middleware)

    def set(self, key, value):
        self.__config[key] = value

    def get(self, key):
        return self.__config[key]

    def param(self, name, callback):
        self.params[name] = callback

    def configure(self, env, callback):
        self.__env_config[env] = callback

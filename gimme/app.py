import os
import sys
from .routes import Routes
from .errors import TemplateError
from .wsgi import WSGIAdapter
from .servers.http import HTTPServer
from .servers.logger import SysLogger
from .middleware import connection_helper
from .engines import Jinja2Engine


class App(object):
    '''
    The central class that ties a Gimme application together.
    
    There are a few configuration parameters that may be passed to App
    objects upon instantiation, although most of the configuration is done
    via middleware.

    Basic usage may look something like the following::

        app = App('some_app')

        # Add middleware.
        app.use(gimme.middleware.session())

        # Add routes to a controller that we have not shown here.
        app.routes.get('/', SomeController.index + 'index.html')
        app.routes.get('/about', SomeController.about + 'about.html')

        # Start the app's development web server.
        app.listen()

    :ivar dirname: Stores the path information from where the app was started
        from.
    :ivar routes: An instance of :class:`gimme.routes.Routes`, which is used
        for mapping routes to controllers, etc.

    :param str name: The name to use for the app in the logger.
    :param engine: The template engine adapter to use.
    :param logger: The log class to use.
    '''

    def __init__(self, name='gimme', engine=Jinja2Engine(), logger=SysLogger):
        self.logger = logger(name)
        self.routes = Routes(self)
        self.engine = engine

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
        '''
        Starts the built-in development webserver.

        :param int port: The port to listen on.
        :param str host: The hostname/IP address to listen on.
        :param http_server: What class to use for the HTTP server.
        '''
        server = http_server(self, host, port)
        server.start()

    def use(self, middleware):
        '''
        Add middleware to the app::


            app.use(gimme.middleware.body_parser())
            app.use(gimme.middleware.session())

        For more information, see :class:`gimme.middleware.Middleware`.

        :param middleware: The middleware to add to the app.
        '''
        self._middleware.append(middleware)

    def set(self, key, value):
        '''
        Sets a config value. These key/value pairs can be used to store
        arbitrary information. Retrieve via :meth:`get() <gimme.app.App.get>`.

        :param key: The key to store under.
        :param value: The value to store.
        '''
        self.__config[key] = value

    def get(self, key):
        '''
        Gets a key from the app, previously set with
        :meth:`set() <gimme.app.App.set>`.

        :param key: The key to fetch
        '''
        return self.__config[key]

    def param(self, name, callback):
        self.params[name] = callback

    def configure(self, env, callback):
        self.__env_config[env] = callback

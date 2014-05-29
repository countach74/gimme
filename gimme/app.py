import os
import sys
from .routes import Routes
from .errors import TemplateError
from .wsgi import WSGIAdapter
#from .servers.http import HTTPServer
from .servers.logger import SysLogger
from .middleware import connection_helper
from .engines import Jinja2Engine
from .modulemonitor import ModuleMonitor
from .util import start_servers
from gevent.pywsgi import WSGIServer
import gevent


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

    :param str name: The name to use for the app in the logger.
    :param engine: The template engine adapter to use.
    :param logger: The log class to use.

    .. attribute:: routes

        An instance of :class:`gimme.routes.Routes`, which is used for
        mapping routes to controllers, etc.

    .. attribute:: dirname

        Stores the path information from where the app was started from.
    '''

    def __init__(self, name='gimme', engine=Jinja2Engine(), logger=SysLogger):
        self.logger = logger(name)
        self.routes = Routes(self)
        self.engine = engine

        self.middleware = []
        self._wsgi = WSGIAdapter(self)
        self._env_config = {}

        self.dirname = os.path.dirname(os.path.abspath(sys.argv[0]))

        # Dictionary to store defined params
        self._params = {}

        # Dictionary to store app config
        self._config = {
            'env': 'development',
            'default headers': {
                'Content-Type': 'text/html; charset=UTF-8',
                'X-PoweredBy': 'Blood, sweat, and tears',
                'X-BadIdea': '; DROP TABLE users;'
            }
        }

    def __call__(self, environ, start_response):
        # Disabled because sort is not implemented in a very useful way (yet)
        # self.routes._sort()
        return self._wsgi.process(environ, start_response)

    def listen(self, host='127.0.0.1', port=8080, server_class=WSGIServer):
        '''
        Starts the built-in development webserver.

        :param int port: The port to listen on.
        :param str host: The hostname/IP address to listen on.
        :param http_server: What class to use for the HTTP server.
        '''
        servers = [self.server(host, port, server_class)]

        if self.get('env') == 'development':
            servers.append(ModuleMonitor(servers[0:1]))

        start_servers(servers)

    def server(self, host='127.0.0.1', port=8080, server_class=WSGIServer):
        return server_class((host, port), self)

    def use(self, middleware):
        '''
        Add middleware to the app::


            app.use(gimme.middleware.body_parser())
            app.use(gimme.middleware.session())

        For more information, see :class:`gimme.middleware.Middleware`.

        :param middleware: The middleware to add to the app.
        '''
        self.middleware.append(middleware)

    def set(self, key, value):
        '''
        Sets a config value. These key/value pairs can be used to store
        arbitrary information. Retrieve via :meth:`get() <gimme.app.App.get>`.

        :param key: The key to store under.
        :param value: The value to store.
        '''
        self._config[key] = value

    def get(self, key, default=None):
        '''
        Gets a key from the app, previously set with
        :meth:`set() <gimme.app.App.set>`.

        :param key: The key to fetch
        '''
        return self._config.get(key, default)

    def param(self, name, callback):
        self.params[name] = callback

    def configure(self, env, callback):
        self._env_config[env] = callback

import gevent
import app as app_
import routes as routes_


class FauxMethod(object):
    pass


class instantiate_controller(object):
    def __init__(self, controller, app=None, middleware=[], uri='/test_endpoint', method='GET'):
        self.__controller = controller
        self.__app = app or app_.App()
        self.__middleware = middleware
        self.__uri = uri
        self.__method = method

    def __getattr__(self, key):
        routes = routes_.Routes(self.__app)
        routes.all(self.__uri, getattr(self.__controller, key))
        request, response = routes.match({
          'PATH_INFO': self.__uri,
          'REQUEST_METHOD': self.__method
        })
        controller = response._render(self.__middleware)
        return getattr(controller, key)


def start_servers(servers):
    greenlets = []
    for i in servers:
        if isinstance(i, gevent.Greenlet):
            i.start()
            greenlets.append(i)
        else:
            greenlet = gevent.Greenlet.spawn(i.start)
            greenlet.start()
            greenlets.append(greenlet)
    gevent.wait(greenlets)


def nested(*managers):
    """Combine multiple context managers into a single nested context manager.

    This function has been deprecated in favour of the multiple manager form
    of the with statement.

    The one advantage of this function over the multiple manager form of the
    with statement is that argument unpacking allows it to be
    used with a variable number of context managers as follows:

      with nested(*managers):
          do_something()

    """
    warn("With-statements now directly support multiple context managers",
         DeprecationWarning, 3)
    exits = []
    vars = []
    exc = (None, None, None)
    try:
        for mgr in managers:
            exit = mgr.__exit__
            enter = mgr.__enter__
            vars.append(enter())
            exits.append(exit)
        yield vars
    except:
        exc = sys.exc_info()
    finally:
        while exits:
            exit = exits.pop()
            try:
                if exit(*exc):
                    exc = (None, None, None)
            except:
                exc = sys.exc_info()
        if exc != (None, None, None):
            # Don't rely on sys.exc_info() still containing
            # the right information. Another exception may
            # have been raised and caught by an exit method
            raise exc[0], exc[1], exc[2]


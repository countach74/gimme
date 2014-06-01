import re
from . import errors
from .request import Request
from .response import Response
from .dotdict import DotDict
from .controller import ErrorController


class PatternMatch(object):
    def __init__(self, pattern, match):
        self.pattern = pattern
        self.match = match
        
    def __repr__(self):
        return "<PatternMatch(%s, %s)>" % (self.pattern, self.match)


class RouteList(list):
    '''
    A subclass of :func:`list` that maintains the same general interface of
    :class:`Route <gimme.routes.Route>`.

    Typically, a ``RouteList`` is created by ``|`` two :class:`Route
    <gimme.routes.Route>` objects together::

        route_list = Route('/somewhere/:param1') | Route('/other/:param1')

    Additional routes can be added by ``|`` more :class:`Route
    <gimme.routes.Route>` objects to the ``RouteList``::

        route1 = Route('/somewhere/:param1')
        route2 = Route('/somewhere_else/:param1')
        route3 = Route('/another_place/:param1')
        route_list = route1 | route2 | route3

    Alternatively, conventional instantiation can be used::

        route_list = RouteList([route1, route2, route3])
    '''
    def __init__(self, data=[], priority=10):
        self.priority = priority
        
        for i in data:
            if isinstance(i, Route):
                self.append(i)
            else:
                self.append(Route(i))

    def __repr__(self):
        return "<RouteList([%s], priority=%s)>" % (', '.join(map(repr, self)),
            self.priority)

    def __or__(self, other):
        self.append(other)
        return self
    
    def __gt__(self, other):
        return self.priority > other.priority
    
    def __lt__(self, other):
        return not self.__gt__(other)
    
    def __eq__(self, other):
        return list.__eq__(self, other) and self.priority == other.priority

    def match(self, uri):
        for i in self:
            match = i.match(uri)
            if match:
                return match
        return None


class Route(object):
    '''
    A common interface for creating and matching route patterns.

    :param regex: Either a string with optional URI parameters (such as
        ``/somewhere`` or ``/somewhere/:param1``), or a regex as created with
        :func:`re.compile`. 
    '''
    _sub_pattern = re.compile(':([a-zA-Z_\-0-9]+)(\?)?')
    _sub_last_pattern = re.compile('\/:([a-zA-Z_\-0-9]+)(\?)?$')
    _strip_pattern = re.compile('\(\?\(__last\)(.*?)\)\(\/\)\?\$$')
    _param_pattern = re.compile('\(\?P\<([a-zA-Z_][a-zA-Z0-9_]*)\>(.*?)\)')

    def __init__(self, regex, priority=10):
        self.priority = priority
        
        if isinstance(regex, basestring):
            self._regex = self._make_regex(regex)
        else:
            self._regex = regex

        self._routes = None
 
    def __gt__(self, other):
        return self.priority > other.priority
    
    def __lt__(self, other):
        return not self.__gt__(other)
    
    def __eq__(self, other):
        return self.priority == other.priority and self._regex == other._regex

    def __repr__(self):
        return "<Route(%s, priority=%s)>" % (self._regex.pattern,
            self.priority)

    def match(self, uri):
        '''
        Tests if the compiled regex pattern matches ``uri``. If it does, an
        instance of :class:`PatternMatch <gimme.routes.PatternMatch>` is
        returned; else ``None``.

        :param uri: The URI to test the regex against.
        :return: Either an instance of :class:`PatternMatch
            <gimme.routes.PatternMatch>` if a match is found or ``None`` if
            no match.
        '''
        match = self._regex.match(uri)
        return PatternMatch(self, match) if match else None

    def _make_regex(self, string):
        if string == '*':
            return re.compile('.*')

        def handle_replace(match):
            return '(?P<%s>[a-zA-Z0-9_\-\.,]+)%s' % (match.group(1),
                match.group(2) or '')

        def handle_last_replace(match):
            return ('(?P<__last>/)?(?(__last)(?P<{0}>[a-zA-Z0-9_\-\.,]+){1})'
                '(/)?').format(
                match.group(1),
                match.group(2) or '')

        pattern = self._sub_last_pattern.sub(handle_last_replace, string)
        pattern = '^%s$' % self._sub_pattern.sub(handle_replace, pattern)
        return re.compile(pattern)

    def __or__(self, other):
        '''
        Create a :class:`RouteList <gimme.routes.RouteList>` object with
        ``self`` and ``other`` in it.

        :param other: Another instance of ``Route``.
        :return: An instance of :class:`RouteList <gimme.routes.RouteList>`.
        '''
        return RouteList([self, other])

    def reverse(self, params):
        orig_pattern = self._regex.pattern

        # Need to strip out a bunch of stuff that gimme adds to routes
        pattern = orig_pattern.replace('(?P<__last>/)?', '/')
        pattern = self._strip_pattern.sub('\\1', pattern)

        string = (self._param_pattern.sub('{\\1}', pattern).format(**params)
            .lstrip('^').rstrip('$'))

        return string if len(string) == 1 else string.rstrip('/')

    def name(self, name):
        if not self._routes:
            raise TypeError("Route not bound to a Routes object.")

        self._name = name
        self._routes._reverse_routes[name] = self

        return self


class RouteMapping(object):
    '''
    Maps a :class:`Route <gimme.routes.Route>` object to a
    :class:`ControllerMethod <gimme.controller.ControllerMethod>` object.

    ``RouteMapping`` objects are generally created by interacting with an
    :class:`application's <gimme.app.App>` :attr:`routes` attribute. For
    example, the following adds a ``RouteMapping`` to an application::

        app.routes.get('/somewhere', SomeController.some_method)

    :param pattern: Either a string to instantiate a :class:`Route
        <gimme.routes.Route>` with, a :class:`Route <gimme.routes.Route>`,
        or a :class:`RouteList <gimme.routes.RouteList>`.
    :param middleware: A list of middleware.
    :param method: An instance of :class:`ControllerMethod
        <gimme.controller.ControllerMethod>`.
    :param match_fn: A callable that can be used to evaluate a match. The
        callable should receive two parameters: ``uri`` and ``environ``, which
        correspond to the URI being matched and the WSGI environ dict,
        respectively.
    '''
    def __init__(self, route, middleware, method, controller=None,
            match_fn=None):
        self.route = route
        self.middleware = middleware
        self.controller = controller
        self.method = method
        self.match_fn = match_fn
        self._name = None
        
    def __gt__(self, other):
        return self.route > other.route
      
    def __lt__(self, other):
        return not self.__gt__(other)
      
    def __eq__(self, other):
        return (
            self.route == other.route and 
            self.middleware == other.middleware and
            self.method == other.method and
            self.match_fn == other.match_fn
        )
    
    def __repr__(self):
        return "<RouteMapping(%s, %s, %s, %s)>" % (self.route,
            self.middleware, self.method, self.match_fn)

    def match(self, environ, match_param='PATH_INFO', context='SCRIPT_NAME'):
        '''
        Test to see if a WSGI environ dict matches the pattern. If it does,
        a :class:`PatternMatch <gimme.routes.PatternMatch>` object is
        returned.

        :param environ: A WSGI environ dict to match against.
        :param match_param: The parameter from the environ dict to consider
            the base URI.
        :return: An instance of :class:`PatternMatch
            <gimme.routes.PatternMatch>` or ``None``.
        '''
        uri = environ.get(match_param, '')
        script_name = environ.get(context, '')

        if uri.startswith(script_name):
            relative_uri = uri[len(script_name):]
        else:
            relative_uri = uri

        if not self.match_fn or (self.match_fn and
                self.match_fn(relative_uri, environ)):
            return self.route.match(relative_uri)


class Routes(object):
    '''
    Manage routes for an application.

    :param app: The Gimme application.
    :param match_param: The WSGI environ variable to use for matching.
    :param strip_trailing_slash: Whether or not trailing slashes should be
        stripped away pre-matching or not. If true, ``/somewhere/`` and
        ``/somewhere`` are equivalent.

    .. attribute:: http404

        A :class:`RouteMapping <gimme.routes.RouteMapping>` pointing to
        :meth:`ErrorController.http404 <gimme.controller.ErrorController.http404>`

    .. attribute:: http500

        A :class:`RouteMapping <gimme.routes.RouteMapping>` pointing to
        :meth:`ErrorController.http500 <gimme.controller.ErrorController.http500>`

    '''

    def __init__(self, app, match_param='PATH_INFO',
            strip_trailing_slash=True):
        self.app = app
        self.match_param = match_param
        self.strip_trailing_slash = strip_trailing_slash

        self._get = []
        self._post = []
        self._put = []
        self._delete = []
        self._all = []
        
        self._sorted = False
        self._controllers = {}
        self._reverse_routes = {}

        self.http404 = RouteMapping('*', [], ErrorController.http404,
            ErrorController(app))
        self.http500 = RouteMapping('*', [], ErrorController.http500,
            ErrorController(app))

    def _add(self, routes_list, pattern, *args, **kwargs):
        middleware = list(args[:-1])
        fn = kwargs.get('fn', None)
        try:
            method = args[-1]
        except IndexError, e:
            raise errors.RouteError("No controller method specified.")

        controller_cls = method.im_class if hasattr(method, 'im_class') else None

        if controller_cls and controller_cls not in self._controllers:
            self._controllers[controller_cls] = controller_cls(self.app)

        route = self._make_route(pattern)
        route_mapping = RouteMapping(route, middleware, method,
            self._controllers.get(controller_cls, None), fn)

        # Bind the route to this Routes object for naming purposes
        route._routes = self

        routes_list.append(route_mapping)

        return route

    def _make_route(self, pattern):
        if isinstance(pattern, (list, tuple)):
            route = RouteList(pattern)
        elif isinstance(pattern, basestring):
            route = Route(pattern)
        elif not isinstance(pattern, (Route, RouteList)):
            raise ValueError("Invalid pattern: %s" % pattern)
        return route

    def get(self, pattern, *args, **kwargs):
        '''
        Add a route that responds only to GET requests.

        The ``pattern`` parameter receives various object types. In its
        simplest form, the pattern may look something like this::

            app.get('/somewhere/:param1', SomeController.some_method)

        Also, a :class:`Route <gimme.routes.Route>` object can be passed::

            app.get(Route('/somewhere/:param1'), SomeController.some_method)

        The advantage to passing a Route object is that Route objects can be
        ``|``'d together, allowing mapping several routes at once to a given
        controller method. For example::

            route1 = Route('/somewhere/:param1')
            route2 = Route('/somewhere_else/:param1')

            app.get(route1 | route2, SomeController.some_method)

        The above creates a :class:`RouteList <gimme.routes.RouteList>`
        object.

        Every other parameter other than ``pattern`` is variable, depending
        on order. In the examples above, the second parameter is an instance
        of :class:`ControllerMethod <gimme.controller.ControllerMethod>`.
        However, middleware can be assigned in between the ``pattern`` and the
        :class:`ControllerMethod <gimme.controller.ControllerMethod>` like
        so::

            app.get('/somewhere/:param1', YourMiddleware,
                SomeController.some_method)

        :param pattern: Either a string that can be instantiated to a
            :class:`Route <gimme.routes.Route>` object, a :class:`Route
            <gimme.routes.Route>` object, or a :class:`RouteList
            <gimme.routes.RouteList>` object.
        :param fn: A callable that is passed to the
            :class:`RouteMapping <gimme.routes.RouteMapping>` object's
            constructor via the ``match_fn`` parameter.
        '''
        return self._add(self._get, pattern, *args, **kwargs)

    def post(self, pattern, *args, **kwargs):
        '''
        Add a route that responds only to POST requests.

        Please reference :meth:`gimme.routes.Routes.get` for more information.
        '''
        return self._add(self._post, pattern, *args, **kwargs)

    def put(self, pattern, *args, **kwargs):
        '''
        Add a route that responds only to PUT requests.

        Please reference :meth:`gimme.routes.Routes.get` for more information.
        '''
        return self._add(self._put, pattern, *args, **kwargs)

    def delete(self, pattern, *args, **kwargs):
        '''
        Add a route that responds only to DELETE requests.

        Please reference :meth:`gimme.routes.Routes.get` for more information.
        '''
        return self._add(self._delete, pattern, *args, **kwargs)

    def all(self, pattern, *args, **kwargs):
        '''
        Add a route that responds to all request types.

        Please reference :meth:`gimme.routes.Routes.get` for more information.
        '''
        return self._add(self._all, pattern, *args, **kwargs)

    def _find_match(self, environ, match_list):
        for i in match_list:
            match = i.match(environ, self.match_param)
            if match:
                params = DotDict(match.match.groupdict())
                default_headers = dict(self.app.get('default headers', []))

                request = Request(environ, params)
                response = Response(200, default_headers)

                return (request, response, i)

    def _sort(self):
        if not self._sorted:
            self._get.sort(reverse=True)
            self._post.sort(reverse=True)
            self._put.sort(reverse=True)
            self._delete.sort(reverse=True)
            self._all.sort(reverse=True)
            self._sorted = True

    def match(self, environ):
        '''
        Find a matching route, if any, and create :class:`Request
        <gimme.request.Request>` and :class:`Response
        <gimme.response.Response>` objects. If no match is found, then the
        objects returned will resolve to the :attr:`Routes.http404
        <gimme.routes.Routes.http404>` attribute.

        :param environ: A WSGI environ dictionary or something similar that
            can be used for matching. Should contain at least
            ``REQUEST_METHOD`` and whichever ``match_param`` was passed to the
            ``Routes`` object (defaults to ``PATH_INFO``).

        :return: A tuple of :class:`Request <gimme.request.Request>` and
            :class:`Response <gimme.response.Response>` objects.
        '''
        request_methods = {
            'GET': self._get,
            'POST': self._post,
            'PUT': self._put,
            'DELETE': self._delete
        }

        request_method = environ['REQUEST_METHOD'].upper()

        if request_method in request_methods:
            match_list = request_methods[request_method]
            result = self._find_match(environ, match_list)
            if result:
                return result

        result = self._find_match(environ, self._all)
        if result:
            return result

        request = Request(environ, None)
        response = Response(404)

        return (request, response, self.http404)

    def get_route_by_name(self, name):
        return self._reverse_routes[name]

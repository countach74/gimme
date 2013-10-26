import re
from .errors import RouteError
from .request import Request
from .response import Response
from .controller import ErrorController


class PatternMatch(object):
    def __init__(self, pattern, match):
        self.pattern = pattern
        self.match = match


class Pattern(object):
    __sub_pattern = re.compile(':([a-zA-Z_\-0-9]+)(\?)?')
    __sub_last_pattern = re.compile('\/:([a-zA-Z_\-0-9]+)(\?)?$')

    def __init__(self, route, regex):
        self.route = route

        if isinstance(regex, str):
            self._regex = self._make_regex(regex)
        else:
            self._regex = regex

    def match(self, uri):
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

        pattern = self.__sub_last_pattern.sub(handle_last_replace, string)
        pattern = '^%s$' % self.__sub_pattern.sub(handle_replace, pattern)
        return re.compile(pattern)


class Route(object):
    def __init__(self, routes, pattern, middleware, method, match_fn=None):
        self.routes = routes
        self.pattern = Pattern(self, pattern)
        self.middleware = middleware
        self.method = method
        self.match_fn = match_fn

    def match(self, environ):
        uri = environ[self.routes.match_param]

        if not self.match_fn or (self.match_fn and
                self.match_fn(uri, environ)):
            return self.pattern.match(uri)


class Routes(object):
    def __init__(self, app, match_param='PATH_INFO',
            strip_trailing_slash=True):
        self.app = app
        self.match_param = match_param
        self.strip_trailing_slash = strip_trailing_slash

        self.__get = []
        self.__post = []
        self.__put = []
        self.__delete = []
        self.__all = []

        self.http404 = Route(self, '*', [], ErrorController.http404)
        self.http500 = Route(self, '*', [], ErrorController.http500)

    def _add(self, routes_list, pattern, *args, **kwargs):
        middleware = list(args[:-1])
        fn = kwargs['fn'] if 'fn' in kwargs else None
        try:
            method = args[-1]
        except IndexError, e:
            raise RouteError("No controller method specified.")
        routes_list.append(Route(self, pattern, middleware, method, fn))

    def get(self, pattern, *args, **kwargs):
        self._add(self.__get, pattern, *args, **kwargs)

    def post(self, pattern, *args, **kwargs):
        self._add(self.__post, pattern, *args, **kwargs)

    def put(self, pattern, *args, **kwargs):
        self._add(self.__put, pattern, *args, **kwargs)

    def delete(self, pattern, *args, **kwargs):
        self._add(self.__delete, pattern, *args, **kwargs)

    def all(self, pattern, *args, **kwargs):
        self._add(self.__all, pattern, *args, **kwargs)

    def _find_match(self, environ, match_list):
        for i in match_list:
            match = i.match(environ)
            if match:
                request = Request(self.app, environ, match)
                response = Response(self.app, i, request)
                return (request, response)

    def match(self, environ):
        request_methods = {
            'GET': self.__get,
            'POST': self.__post,
            'PUT': self.__put,
            'DELETE': self.__delete
        }

        request_method = environ['REQUEST_METHOD'].upper()

        if request_method in request_methods:
            match_list = request_methods[request_method]
            result = self._find_match(environ, match_list)
            if result:
                return result

        result = self._find_match(environ, self.__all)
        if result:
            return result

        request = Request(self.app, environ, None)
        response = Response(self.app, self.http404, response)
        return (request, response)

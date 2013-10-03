import re
from .errors import RouteError
from .request import Request


class PatternMatch(object):
  def __init__(self, pattern, match):
    self.pattern = pattern
    self.match = match


class Pattern(object):
  __sub_pattern = re.compile(':([a-zA-Z_\-0-9]+)(\?)?')

  def __init__(self, route, regex):
    self.route = route

    if isinstance(regex, str):
      self.regex = self.make_regex(regex)
    else:
      self.regex = regex

  def match(self, uri):
    match = self.regex.match(uri)
    return PatternMatch(self, match) if match else None

  def make_regex(self, string):
    string = '^%s$' % string
    def handle_replace(match):
      return '(?P<%s>[a-zA-Z0-9_\-\.,]+)%s' % (match.group(1),
        match.group(2) or '')
    pattern = re.sub(self.__sub_pattern, handle_replace, string)
    return re.compile(pattern)


class Route(object):
  def __init__(self, routes, pattern, middleware, method):
    self.routes = routes
    self.pattern = Pattern(self, pattern)
    self.middleware = middleware
    self.method = method

  def match(self, uri):
    return self.pattern.match(uri)


class Routes(object):
  def __init__(self, app, match_param='REQUEST_URI', strip_trailing_slash=True):
    self.match_param = match_param
    self.strip_trailing_slash = strip_trailing_slash

    self.__get = []
    self.__post = []
    self.__put = []
    self.__delete = []
    self.__all = []

  def _add(self, routes_list, pattern, *args):
    middleware = args[:-1]
    try:
      method = args[-1]
    except IndexError, e:
      raise RouteError("No controller method specified.")
    routes_list.append(Route(self, pattern, middleware, method))

  def get(self, pattern, *args):
    self._add(self.__get, pattern, *args)

  def post(self, pattern, *args):
    self._add(self.__post, pattern, *args)

  def put(self, pattern, *args):
    self._add(self.__put, pattern, *args)

  def delete(self, pattern, *args):
    self._add(self.__delete, pattern, *args)

  def all(self, pattern, *args):
    self._add(self.__all, pattern, *args)

  def match(self, environ):
    request_methods = {
      'GET': self.__get,
      'POST': self.__post,
      'PUT': self.__put,
      'DELETE': self.__delete
    }

    request_method = environ['REQUEST_METHOD'].upper()
    uri = environ[self.match_param]

    if request_method in request_methods:
      match_list = request_methods[request_method]
      for i in match_list:
        match = i.match(uri)
        if match:
          return Request(self.app, environ, match)
    return None

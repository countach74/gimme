from .headers import RequestHeaders
from .dotdict import DotDict
from .uri import QueryString


class Request(object):
  def __init__(self, app, environ, match=None):
    self.app = app
    self.environ = environ
    self.match = match
    self.headers = RequestHeaders()
    self.wsgi = RequestHeaders()
    self.params = DotDict(match.match.groupdict())

    self._populate_headers(environ)

    self.query = QueryString(self.headers.query_string
      if 'query_string' in self.headers else '')

  def _populate_headers(self, environ):
    for k, v in environ.iteritems():
      key = k.lower()
      if key.startswith('http_'):
        self.headers[key[5:]] = v
      elif key.startswith('wsgi.'):
        self.wsgi[key[5:]] = v
      else:
        self.headers[key] = v

  def get(self, key):
    return self.headers[key.replace('-', '_')]

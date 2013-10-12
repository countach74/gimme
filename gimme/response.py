import time
import datetime
from .headers import ResponseHeaders


class Response(object):
  _status_code_map = {
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi-Status',
    208: 'Already Reported',
    226: 'IM Used',
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: 'Switch Proxy',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Requred',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Request Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",
    419: 'Authentication Timeout',
    420: 'Enhance Your Calm',
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    425: 'Unordered Collection',
    426: 'Upgrade Required',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    444: 'No Response',
    451: 'Unavailable For Legal Reasons',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',
    507: 'Insufficient Storage',
    508: 'Loop Detected',
    509: 'Bandwidth Limit Exceeded',
    510: 'Not Extended',
    511: 'Network Authentication Required',
    522: 'Connection Timed Out'
  }

  def __init__(self, app, route):
    self.app = app
    self.route = route
    self._status = '200 OK'

    try:
      self.headers = ResponseHeaders(dict(app.get('default headers')))
    except KeyError, e:
      self.headers = ResponseHeaders()

    self._controller_class = route.method.im_class
    self._method_name = route.method.__name__

  def status(self, status):
    if isinstance(status, int):
      self._status = '%s %s' % (status, self._status_code_map[status])
    else:
      self._status = status
    return self

  @property
  def status_code(self):
    return int(self._status.split(None, 1)[0])

  @property
  def status_message(self):
    return int(self._status.split(None, 1)[1])
    
  def _prepare(self, method):
    self.body = method()
    
  def set(self, key, value):
    self.headers[key] = value
    return self
    
  def get(self, key):
    return self.headers[key]

  def redirect(self, path, code=302):
    self.status(code).location(path)

  def location(self, path):
    self.set('Location', path)

  def type(self, content_type):
    self.set('Content-Type', content_type)

  def cookie(self, key, value, expires=None, http_only=False, secure=False, path='/', domain=None):
    cookie_string = ['%s=%s' % (key, value)]

    if domain:
      cookie_string.append('Domain=%s' % domain)

    if path:
      cookie_string.append('Path=%s' % path)

    if expires:
      if isinstance(expires, int):
        date = datetime.datetime.fromutctimestamp(time.mktime(time.gmtime()))
      elif isinstance(expires, datetime.datetime):
        date = expires
      else:
        date = datetime.datetime.utcnow()
      cookie_string.append('Expires=%s' % date.stftime('%a, %d %b %Y %H:%M:%S GMT'))

    if secure:
      cookie_string.append('Secure')

    if http_only:
      cookie_string.append('HttpOnly')

    self.set('Set-Cookie', '; '.join(cookie_string))

import traceback
import time
import datetime
import contextlib
import mimetypes
import re
import sys
from .dotdict import DotDict
from .headers import ResponseHeaders, Header
from .controller import ErrorController
import gimme.errors


class Response(object):
    _charset_pattern = re.compile('(.*?); charset=(.*)$')
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
        401: 'Not Authorized',
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

    mimetypes.init()

    def __init__(self, app, route, request):
        self.app = app
        self.route = route
        self.request = request
        self._status = '200 OK'

        try:
            self.headers = ResponseHeaders(dict(app.get('default headers')))
        except KeyError, e:
            self.headers = ResponseHeaders()

        self._controller_class = route.method.im_class
        self._method_name = route.method.__name__
        self.body = None

        # Storage for request-specific local data
        self.locals = DotDict()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if isinstance(status, int):
            self._status = '%s %s' % (status, self._status_code_map[status])
        else:
            self._status = status
        

    @property
    def status_code(self):
        return int(self._status.split(None, 1)[0])

    @property
    def status_message(self):
        return self._status.split(None, 1)[1]

    def _make_next(self, i, fn, method, next_fns):
        if fn is method:
            def next_():
                self.body = fn()
        else:
            def next_():
                fn(self.request, self, next_fns[i-1])
        return next_

    def _render(self, middleware=None):
        controller = self._controller_class(self.app, self.request, self)
        method = getattr(controller, self._method_name)

        if middleware is None:
            middleware = (self.app._middleware + self.route.middleware
                + [method])
        elif not middleware:
            middleware = [method]

        next_fns = []

        for i, fn in enumerate(list(reversed(middleware))):
            next_fns.append(self._make_next(i, fn, method, next_fns))

        next_fns[-1]()

    def set(self, key, value):
        self.headers[key] = value
        return self

    def get(self, key):
        return self.headers[key]

    def redirect(self, path, code=302):
        self.status = code
        self.location = path

    @property
    def location(self):
        return self.get('Location')

    @location.setter
    def location(self, path):
        self.set('Location', path)

    @property
    def type(self):
        return self.get('Content-Type')

    @type.setter
    def type(self, content_type):
        self.set('Content-Type', content_type)

    def cookie(self, key, value, expires=None, http_only=False, secure=False,
            path='/', domain=None):
        cookie_string = ['%s=%s' % (key, value)]

        if domain:
            cookie_string.append('Domain=%s' % domain)

        if path:
            cookie_string.append('Path=%s' % path)

        if expires:
            if isinstance(expires, int):
                date = datetime.datetime.utcfromtimestamp(time.mktime(
                    time.gmtime(time.time() + expires)))
            elif isinstance(expires, datetime.datetime):
                date = expires
            else:
                date = datetime.datetime.utcnow()
            cookie_string.append('Expires=%s' % date.strftime(
                '%a, %d %b %Y %H:%M:%S GMT'))

        if secure:
            cookie_string.append('Secure')

        if http_only:
            cookie_string.append('HttpOnly')

        self.headers.add_header(Header('Set-Cookie', '; '.join(cookie_string)))

    def clear_cookie(self, key):
        expires = datetime.datetime.fromtimestamp(0)
        self.cookie(key, 'deleted', expires=expires)

    def attachment(self, filename=None):
        if filename:
            self.headers['Content-Disposition'] = ('attachment; filename="%s"'
                % filename)
            mimetype, encoding = mimetypes.guess_type(filename)
            if mimetype:
                self.type = mimetype
        else:
            self.headers['Content-Disposition'] = 'attachment';

    attachment = property(None, attachment)

    @property
    def charset(self):
        if 'Content-Type' in self.headers:
            header = self.headers['Content-Type']
            match = self._charset_pattern.match(header.value)
            if match:
                return match.group(2)
        return None

    @charset.setter
    def charset(self, value):
        if 'Content-Type' in self.headers:
            header = self.headers['Content-Type']
        else:
            header = Header('Content-Type', 'text/html')
            self.headers.add_header(header)

        match = self._charset_pattern.match(header.value)
        if match:
            header.value = '%s; charset=%s' % (
                match.group(1), value)
        else:
            header.value = '%s; charset=%s' % (
                header.value, value)

    def links(self, links):
        buffer_ = []
        for k, v in links.iteritems():
            buffer_.append('<%s>; rel="%s"' % (v, k))
        self.headers['Link'] = ', '.join(buffer_)

    links = property(None, links)

    def render(self, template, params):
        raise NotImplementedError("Response.render() not implemented!")

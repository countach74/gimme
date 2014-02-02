import re
from .headers import RequestHeaders
from .dotdict import DotDict
from .uri import QueryString
from .errors import AcceptFormatError
from .parsers.contenttype import ContentType
from .parsers.accepted import AcceptedList


class Request(object):
    _host_pattern = re.compile('^([^:]*)(:[0-9]+)?')

    def __init__(self, app, environ, match=None):
        self.app = app
        self.environ = environ
        self.headers = RequestHeaders()
        self.wsgi = RequestHeaders()
        self.params = DotDict(match.match.groupdict() if match else {})
        self.__raw_body = None

        self._populate_headers(environ)

        self.query = QueryString(self.headers.get('query_string', ''))

        self.accepted = AcceptedList.parse(
            self.headers.get('accept', ''), ContentType)

        self.accepted_languages = AcceptedList.parse(
            self.headers.get('accept_language', ''))

        self.accepted_charsets = AcceptedList.parse(
            self.headers.get('accept_charset', ''))

        self.cookies = self.headers.get('cookie', '')
        self.type = (ContentType(self.headers.content_type) if 'content_type'
            in self.headers else None)

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

    def accepts(self, content_type):
        return content_type in self.accepted

    def accepts_language(self, language):
        return language in self.accepted_languages

    def accepts_charset(self, charset):
        return charset in self.accepted_charsets

    @property
    def raw_body(self):
        if self.__raw_body is None:
            if (self.headers.get('request_method', None) in ('PUT', 'POST')
                    and 'content_length' in self.headers):
                content_length = int(self.headers.content_length)
                self.__raw_body = self.wsgi.input.read(content_length)
            else:
                self.__raw_body = ''
        return self.__raw_body

    def param(self, key):
        if key in self.params:
            return self.params[key]
        elif hasattr(self, 'body') and key in self.body:
            return self.body[key]
        elif key in self.query:
            return self.query[key]
        raise KeyError(key)

    @property
    def xhr(self):
        return self.headers.get('x_requested_with', None) == 'XMLHttpRequest'

    @property
    def path(self):
        return self.headers.get('path_info', None)

    @property
    def host(self):
        raw_host = self.headers.get('host', '')
        return self._host_pattern.match(raw_host).group(1)

    @property
    def subdomains(self):
        split = self.headers.get('host', '').split('.')
        return split[:-2] if len(split) > 2 else []

    @property
    def ip(self):
        return self.headers.get('remote_addr', None)

    @property
    def secure(self):
        '''
        Right now, Gimme only runs in standard HTTP mode. SSL should be
        implemented at the HTTP server end and piped to Gimme via FastCGI.
        '''
        return False

    @property
    def original_url(self):
        return self.headers.get('request_uri', None)

    @property
    def protocol(self):
        '''
        Gimme only supports HTTP as of the time of this writing.
        '''
        return 'http'

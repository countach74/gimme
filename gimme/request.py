import re
from .headers import RequestHeaders
from .dotdict import DotDict
from .uri import QueryString
from .errors import AcceptFormatError
from .parsers.contenttype import ContentType
from .parsers.accepted import AcceptedList


class Request(object):
    '''
    The Request class is responsible for parsing the request headers and body
    into Pythonic shindigs that are (supposed to be) very easy to work with.

    :ivar app: The Gimme application.
    :ivar environ: The WSGI environ dict.
    :ivar headers: The request headers (an instance of :class:`gimme.headers.RequestHeaders`).
    :ivar wsgi: The WSGI headers. Also an instance of :class:`gimme.headers.RequestHeaders`.
    :ivar params: A :class:`gimme.dotdict.DotDict` of the parameters from the
        route URI.
    :ivar query: The query string in a dictionary-like object.
    :ivar accepted: A handy parsing of the HTTP "Accept" header. An instance
        of :class:`gimme.parsers.accepted.AcceptedList`.
    :ivar accepted_languages: A handy parsing of the HTTP "Accept-Language"
        header. An instance of :class:`gimme.parsers.accepted.AcceptedList`.
    :ivar accepted_charsets: A handy parsing of the HTTP "Accept-Charset"
        header. An instance of :class:`gimme.parsers.accepted.AcceptedList`.
    :ivar cookies: The raw HTTP "Cookie" string.
    :ivar type: Either an instance of
        :class:`gimme.parsers.contenttype.ContentType` if the HTTP header
        "Content-Type" is present or ``None``.

    :param app: The Gimme application.
    :param environ: The WSGI environ dict.
    :param match: The matching route, if any.
    '''
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
        '''
        Return the specified request header.

        :param key: The header to return.
        '''
        return self.headers[key.replace('-', '_')]

    def accepts(self, content_type):
        '''
        Tests if a given content type is in the HTTP "Accept" header.

        :param content_type: The content type to check for.
        '''
        return content_type in self.accepted

    def accepts_language(self, language):
        '''
        Tests if a given language is in the HTTP "Accept-Language" header.

        :param language: The language to check for.
        '''
        return language in self.accepted_languages

    def accepts_charset(self, charset):
        '''
        Tests if a given charset is in the HTTP "Accept-Charset" header.

        :param charset: The charset to check for.
        '''
        return charset in self.accepted_charsets

    @property
    def raw_body(self):
        '''
        The raw request body.
        '''
        if self.__raw_body is None:
            if (self.headers.get('request_method', None) in ('PUT', 'POST')
                    and 'content_length' in self.headers):
                content_length = int(self.headers.content_length)
                self.__raw_body = self.wsgi.input.read(content_length)
            else:
                self.__raw_body = ''
        return self.__raw_body

    def param(self, key):
        '''
        A simple helper method that looks for a given key in three places:
        self.params, self.body, and self.query.

        :param key: The parameter to look for.
        '''
        if key in self.params:
            return self.params[key]
        elif hasattr(self, 'body') and key in self.body:
            return self.body[key]
        elif key in self.query:
            return self.query[key]
        raise KeyError(key)

    @property
    def xhr(self):
        '''
        Whether or not the HTTP header "X-Requested-With" is present and
        set to "XMLHttpRequest".
        '''
        return self.headers.get('x_requested_with', None) == 'XMLHttpRequest'

    @property
    def path(self):
        '''
        A shortcut for the "PATH_INFO" environ parameter.
        '''
        return self.headers.get('path_info', None)

    @property
    def host(self):
        '''
        A shortcut for the HTTP "Host" header.

        *Note: Strips any port off of the header.*
        '''
        raw_host = self.headers.get('host', '')
        return self._host_pattern.match(raw_host).group(1)

    @property
    def subdomains(self):
        '''
        A list of subdomains per the ``host`` attribute.
        '''
        split = self.headers.get('host', '').split('.')
        return split[:-2] if len(split) > 2 else []

    @property
    def ip(self):
        '''
        A shortcut for the "REMOTE_ADDR" environ parameter.
        '''
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
        '''
        A shortcut for the "REQUEST_URI" environ parameter.
        '''
        return self.headers.get('request_uri', None)

    @property
    def protocol(self):
        '''
        Gimme only supports HTTP as of the time of this writing.
        '''
        return 'http'

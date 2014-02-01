import re
from .headers import RequestHeaders
from .dotdict import DotDict
from .uri import QueryString
from .errors import AcceptFormatError
from .parsers.contenttype import ContentType


class AcceptFormatter(object):
    _pattern = re.compile('(?P<value>[a-zA-Z0-9_\-]+)'
        '(?:;q=(?P<priority>[0-9]*\.?[0-9]*))?')

    def __init__(self, data):
        self._data = data
        self._match = self._pattern.match(data)

        if not self._match:
            raise AcceptFormatError("Invalid accept format")

        groups = self._match.groupdict()
        self.value = groups['value']
        self.priority = (
            float(groups['priority'])
            if groups['priority'] is not None else 1)

    def __repr__(self):
        return "<AcceptFormatter(%s, priority %s)>" % (
            self.value, self.priority)

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return other == self.value


class AcceptMimeFormatter(object):
    _pattern = re.compile('(?P<type>[a-zA-Z0-9\-_\*]+)/(?P<subtype>'
        '[a-zA-Z0-9\-_\*]+)(?:;q=(?P<priority>[0-9]*[\.]?[0-9]*))?')
    _mime_pattern = re.compile('(?P<type>[a-zA-Z0-9\-_\*]+)/'
        '(?P<subtype>[a-zA-Z0-9\-_\*]+)')

    def __init__(self, data):
        self._data = data
        self._match = self._pattern.match(data)
        if not self._match:
            raise AcceptFormatError("Invalid accept format")
        else:
            groups = self._match.groupdict()
            self.type = groups['type']
            self.subtype = groups['subtype']
            self.priority = (
                float(groups['priority'])
                if groups['priority'] is not None else 1)

    def __repr__(self):
        return "<AcceptMimeFormatter(%s/%s, priority %s)>" % (
            self.type, self.subtype, self.priority)

    def __str__(self):
        return '%s/%s' % (self.type, self.subtype)

    def __eq__(self, other):
        if self.type == '*':
            return True

        match = self._mime_pattern.match(other)
        if match:
            data = match.groupdict()

            if data['type'] == self.type and data['subtype'] == self.subtype:
                return True
            elif self.subtype == '*':
                return True
        return False


class AcceptedList(object):
    _separator = re.compile('\s*,\s*')

    def __init__(self, raw, formatter=AcceptFormatter):
        self._raw = raw
        self._formatter = formatter
        self._data = list(self._parse(raw))

    def _parse(self, raw):
        split = self._separator.split(self._raw)
        for i in split:
            try:
                yield self._formatter(i)
            except AcceptFormatError:
                continue

    def get_items_by_priority(self):
        return sorted(self._data, key=lambda x: x.priority, reverse=True)

    def get_highest_priority(self):
        try:
            return self.get_items_by_priority()[0]
        except IndexError:
            return None

    def get_highest_priority_for_mime(self, mime):
        candidates = []

        if not isinstance(mime, list):
            mime = [mime]

        for i in self.get_items_by_priority():
            for j in mime:
                if i == j:
                    candidates.append(j)

        return candidates[0] if len(candidates) else None

    def as_list(self):
        return map(str, self.get_items_by_priority())

    def __iter__(self):
        for i in self._data:
            yield i

    def __contains__(self, key):
        for i in self._data:
            if i == key:
                return True
        return False

    def __repr__(self):
        items = map(str, self._data)
        return '<AcceptedList(%s)>' % ', '.join(items)


class Request(object):
    _host_pattern = re.compile('^([^:]*)(:[0-9]+)?')

    def __init__(self, app, environ, match=None):
        self.app = app
        self.environ = environ
        self.match = match
        self.headers = RequestHeaders()
        self.wsgi = RequestHeaders()
        self.params = DotDict(match.match.groupdict() if match else {})
        self.__raw_body = None

        self._populate_headers(environ)

        self.query = QueryString(self.headers.query_string
            if 'query_string' in self.headers else '')

        self.accepted = AcceptedList(self.headers.accept if 'accept' in
            self.headers else '', formatter=AcceptMimeFormatter)

        self.accepted_languages = AcceptedList(self.headers.accept_language
            if 'accept_language' in self.headers else '')

        self.accepted_charsets = AcceptedList(self.headers.accept_charset
            if 'accept_charset' in self.headers else '')

        self.cookies = self.headers.cookie if 'cookie' in self.headers else ''
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
            if ('request_method' in self.headers and
                    self.headers.request_method in ('PUT', 'POST') and
                    'content_length' in self.headers):
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
        return ('x_requested_with' in self.headers and
            self.headers.x_requested_with == 'XMLHttpRequest')

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

import abc
import re
import os
import random
import uuid
from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from multipart import MultipartParser
from .dotdict import DotDict
from .ext.session import Session as _Session


class Middleware(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, app, request, response):
        self.app = app
        self.request = request
        self.response = response

    def __enter__(self):
        self.enter()

    def __exit__(self, exc_type, exc_value, traceback):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.traceback = traceback
        self.exit()

    @abc.abstractmethod
    def enter(self):
        pass

    @abc.abstractmethod
    def exit(self):
        pass


def connection_helper(connection='close'):
    class ConnectionHelper(Middleware):
        def enter(self):
            pass

        def exit(self):
            self.response.headers['Connection'] = connection
            self.response.headers['Content-Length'] = str(len(self.response.body))

    return ConnectionHelper


def static(path, expose_as='/'):
    expose_as = (expose_as or os.path.basename(path)).strip('/')
    pattern = re.compile('^/%s.*' % re.escape(expose_as))

    import mimetypes
    mimetypes.init()

    class Static(Middleware):
        def enter(self):
            match = pattern.match(self.request.headers.path_info)
            self._file = None
            self._local_path = None

            if match:
                self._local_path = self._get_local_path(
                    self.request.headers.path_info)
                if self._local_path:
                    self.response.set('Content-Type', mimetypes.guess_type(
                        self._local_path)[0])

        def exit(self):
            if self._local_path:
                self.response.status(200)
                try:
                    with open(self._local_path, 'r') as f:
                        self._serve(f)
                except OSError, e:
                    pass

        def _serve(self, f):
            self.response.body = f.read()

        def _get_local_path(self, local_path):
            local_path = local_path.strip('/')[len(expose_as):].lstrip('/')
            temp_path = os.path.join(path, local_path)
            if temp_path.startswith(path) and os.path.isfile(temp_path):
                return temp_path
            else:
                return None

    return Static


def cookie_parser():
    class CookieParser(Middleware):
        def enter(self):
            try:
                data = self.request.cookies.split('; ')
            except AttributeError:
                self.request.cookies = DotDict()
                return

            self.request.cookies = DotDict()
            for i in data:
                if i:
                    split = i.split('=', 1)
                    if split:
                        self.request.cookies[split[0]] = split[1]

        def exit(self):
            pass

    return CookieParser


def session(cache='gimme.cache.memory', session_cookie='gimme_session',
        make_session_key=uuid.uuid4, expiration_time=3600, **kwargs):

    region = make_region().configure(cache, expiration_time=expiration_time,
        **kwargs)

    class Session(Middleware):
        def enter(self):
            self._new_session = False
            self.request.session = self._load_session()

        def exit(self):
            if self.request.session._state.is_dirty() or self._new_session:
                self.request.session.save()

        def _load_session(self):
            try:
                key = self.request.cookies[session_cookie]
            except KeyError:
                return self._create_session()

            session_data = region.get(key)

            if session_data != NO_VALUE:
                return _Session(region, key, session_data)
            else:
                return self._create_session()

        def _create_session(self):
            self._new_session = True
            key = str(make_session_key())
            self.response.set('Set-Cookie', '%s=%s' % (session_cookie, key))
            new_session = _Session(region, key, {})
            return new_session

    return Session


def json():
    from json import loads as decode_json

    class Json(Middleware):
        def enter(self):
            if ('content_type' in self.request.headers and
                    self.request.headers.content_type.startswith('application/json')):

                try:
                    parsed_data = decode_json(self.request.raw_body)
                except ValueError:
                    self.request.body = DotDict({})
                else:
                    self.request.body = DotDict(parsed_data)

        def exit(self):
            pass

    return Json


def urlencoded(use_as_fallback=True):
    from .uri import QueryString

    class UrlEncoded(Middleware):
        def enter(self):
            if (('content_type' in self.request.headers and
                    self.request.headers.content_type.startswith(
                    'application/x-www-form-urlencoded'))):

                self.request.body = QueryString(self.request.raw_body)

        def exit(self):
            pass

    return UrlEncoded


def multipart():
    multipart_pattern = re.compile('^multipart/form-data; boundary=(.*)', re.I)

    class Multipart(Middleware):
        def enter(self):
            if ('content_type' in self.request.headers and
                    'request_method' in self.request.headers and
                    self.request.headers.request_method in ('PUT', 'POST')):

                match = multipart_pattern.match(
                    self.request.headers.content_type)

                if match:
                    mp = MultipartParser(self.request.wsgi.input, boundary=
                        match.group(1))
                    for i in mp:
                        if i.filename:
                            self.request.body[i.name] = i
                        else:
                            self.request.body[i.name] = i.value

        def exit(self):
            pass

    return Multipart


def body_parser(json_args={}, urlencoded_args={}, multipart_args={}):
    json_parser = json(**json_args)
    urlencoded_parser = urlencoded(**urlencoded_args)
    multipart_parser = multipart(**multipart_args)

    class BodyParser(Middleware):
        def __init__(self, *args, **kwargs):
            Middleware.__init__(self, *args, **kwargs)
            self._json = json_parser(*args, **kwargs)
            self._multipart = multipart_parser(*args, **kwargs)
            self._urlencoded = urlencoded_parser(*args, **kwargs)

        def enter(self):
            self._json.enter()
            self._multipart.enter()
            self._urlencoded.enter()

        def exit(self):
            pass

    return BodyParser


def method_override():
    from .uri import QueryString
    multipart_pattern = re.compile('^multipart/form-data; boundary=(.*)', re.I)

    class MethodOverride(Middleware):
        def enter(self):
            if ('content_type' in self.request.headers and
                    self.request.headers.content_type ==
                    'application/x-www-form-urlencoded'):
                query_string = QueryString(self.request.raw_body)
                if '_method' in query_string:
                    self.request.headers.request_method = query_string._method

        def exit(self):
            pass

    return MethodOverride


def compress():
    import zlib

    class Compress(Middleware):
        def enter(self):
            pass

        def exit(self):
            if 'accept_encoding' in self.request.headers:
                if ('deflate' in
                        self.request.headers.accept_encoding.split(',')):
                    compressed = zlib.compress(self.response.body)
                    self.response.headers['Content-Encoding'] = 'deflate'
                    self.response.headers['Content-Length'] = str(
                        len(compressed))
                    self.response.body = compressed

    return Compress


def profiler(fn=None, pr=None):
    import cProfile

    if pr is None:
        pr = cProfile.Profile()

    class Profiler(Middleware):
        def enter(self):
            pr.enable()

        def exit(self):
            pr.disable()
            if fn:
                fn(pr)

    return Profiler

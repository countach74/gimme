import abc
import re
import os
import random
import uuid
import json as jsonlib
from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from .parsers.multipart import MultipartParser
from .dotdict import DotDict
from .ext.session import Session as _Session


class connection_helper(object):
    def __init__(self, connection='close'):
        self.connection = connection

    def __call__(self, request, response, next_):
        next_()
        response.headers['Connection'] = self.connection
        response.headers['Content-Length'] = str(len(response.body))


class static(object):
    def __init__(self, path, expose_as='/'):
        self.path = path
        self.expose_as = (expose_as or os.path.basename(path)).strip('/')
        self.pattern = re.compile('^/%s.*' % re.escape(self.expose_as))

        self.mimetypes = __import__('mimetypes')
        self.mimetypes.init()

    def __call__(self, request, response, next_):
        match = self.pattern.match(request.headers.path_info)
        local_path = None

        if match:
            local_path = self._get_local_path(
                request.headers.path_info)
            if local_path:
                response.set('Content-Type', self.mimetypes.guess_type(
                    local_path)[0])
                response.status = 200
                try:
                    with open(local_path, 'r') as f:
                        response.body = f.read()
                except OSError, e:
                    pass
            else:
                next_()
        else:
            next_()

    def _get_local_path(self, local_path):
        local_path = local_path.strip('/')[len(self.expose_as):].lstrip('/')
        temp_path = os.path.join(self.path, local_path)
        if temp_path.startswith(self.path) and os.path.isfile(temp_path):
            return temp_path
        else:
            return None


class cookie_parser(object):
    def __call__(self, request, response, next_):
        try:
            data = request.cookies.split('; ')
        except AttributeError:
            request.cookies = DotDict()
            return

        request.cookies = DotDict()
        for i in data:
            if i:
                split = i.split('=', 1)
                if split:
                    request.cookies[split[0]] = split[1]

        next_()


class session(object):
    def __init__(self, cache='gimme.cache.memory',
            session_cookie='gimme_session', make_session_key=uuid.uuid4,
            expiration_time=60*60*24*7, **kwargs):

        self.cache = cache
        self.session_cookie = session_cookie
        self.make_session_key = make_session_key
        self.expiration_time = expiration_time

        self.region = make_region().configure(cache,
            expiration_time=expiration_time, **kwargs)

    def __call__(self, request, response, next_):
        request.session = self._load_session(request, response)

        next_()

        if request.session._state.is_dirty():
            request.session.save()

    def _load_session(self, request, response):
        try:
            key = request.cookies[self.session_cookie]
        except KeyError:
            return self._create_session(response)

        session_data = self.region.get(key)

        if session_data != NO_VALUE:
            return _Session(self.region, key, session_data)
        else:
            return self._create_session(response)

    def _create_session(self, response):
        key = str(self.make_session_key())
        response.set('Set-Cookie', '%s=%s' % (self.session_cookie, key))
        new_session = _Session(self.region, key, {}, True)
        return new_session


class json(object):
    def __call__(self, request, response, next_):
        if not hasattr(request, 'body'):
            request.body = DotDict()
 
        if ('content_type' in request.headers and
                request.headers.content_type.startswith('application/json')):

            try:
                parsed_data = jsonlib.loads(request.raw_body)
            except ValueError:
                pass
            else:
                for k, v in parsed_data.iteritems():
                    request.body[k] = v

        next_()


class urlencoded(object):
    from .uri import QueryString

    def __init__(self, use_as_fallback=False):
        self.use_as_fallback = use_as_fallback

    def __call__(self, request, response, next_):
        if not hasattr(request, 'body'):
            request.body = DotDict()
 
        if ('content_type' in request.headers and
                request.headers.content_type.startswith(
                'application/x-www-form-urlencoded')):

            qs = self.QueryString(request.raw_body)
            for k, v in qs.iteritems():
                request.body[k] = v

        next_()


class multipart(object):
    multipart_pattern = re.compile('^multipart/form-data; boundary=(.*)', re.I)

    def __call__(self, request, response, next_):
        if not hasattr(request, 'body'):
            request.body = DotDict()

        if not hasattr(request, 'files'):
            request.files = DotDict()
            
        if ('content_type' in request.headers and
                'request_method' in request.headers and
                request.headers.request_method in ('PUT', 'POST')):

            match = self.multipart_pattern.match(
                request.headers.content_type)

            if match:
                mp = MultipartParser(match.group(1), request.wsgi.input)
                for name, mp_file in mp.iteritems():
                    if mp_file.value:
                        request.body[name] = mp_file.value
                    else:
                        request.files[name] = mp_file

        next_()


class body_parser(object):
    def __init__(self, json_args={}, urlencoded_args={}, multipart_args={}):
        self.json_parser = json(**json_args)
        self.urlencoded_parser = urlencoded(**urlencoded_args)
        self.multipart_parser = multipart(**multipart_args)

    def _dummy_next(self):
        pass

    def __call__(self, request, response, next_):
        self.json_parser(request, response, self._dummy_next)
        self.urlencoded_parser(request, response, self._dummy_next)
        self.multipart_parser(request, response, self._dummy_next)

        next_()


class method_override(object):
    from .uri import QueryString

    def __init__(self):
        self.multipart_pattern = re.compile('^multipart/form-data; boundary=(.*)', re.I)

    def __call__(self, request, response, next_):
        if ('content_type' in request.headers and
                request.headers.content_type ==
                'application/x-www-form-urlencoded'):
            query_string = self.QueryString(request.raw_body)
            if '_method' in query_string:
                request.headers.request_method = query_string._method
        next_()


class compress(object):
    def __init__(self):
        self.zlib = __import__('zlib')

    def __call__(self, request, response, next_):
        next_()
        if 'accept_encoding' in request.headers:
                if ('deflate' in
                        request.headers.accept_encoding.split(',')):
                    try:
                        compressed = self.zlib.compress(response.body)
                    except TypeError:
                        pass
                    else:
                        response.headers['Content-Encoding'] = 'deflate'
                        response.headers['Content-Length'] = str(len(compressed))
                        response.body = compressed


class profiler(object):
    def ___init__(self, fn=None, pr=None):
        self.fn = fn
        self.pr = pr
        self.cProfile = __import__('cProfile')

    def __call__(self, request, response, next_):
        if self.pr is None:
            self.pr = cProfile.Profile()

        pr.enable()
        next_()
        pr.disable()
        if self.fn:
            self.fn(self.pr)

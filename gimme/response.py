import traceback
import time
import datetime
import mimetypes
import re
import sys

try:
    from contextlib import nested
except ImportError:
    from util import nested

from .dotdict import DotDict
from .headers import ResponseHeaders, Header
from .controller import ErrorController
from .parsers.status import StatusCode
from .parsers.contenttype import ContentType
from .output import OutputBody
import gimme.errors


class Response(object):
    '''
    The Response class is responsible for aggregating all of the information
    required for generating a response and for rendering said response.

    :ivar app: The Gimme application.
    :ivar route: The route that matched the request/response objects.
    :ivar request: The request object.
    :ivar headers: An instance of :class:`gimme.headers.ResponseHeaders` that
        will eventually be converted to a string appropriate for the HTTP
        response headers.
    :ivar body: The body of response.
    :ivar locals: An instance of :class:`gimme.dotdict.DotDict` that is
        intended to store arbitrary information that is unique to a given
        response object.
    '''

    _charset_pattern = re.compile('(.*?); charset=(.*)$')
    mimetypes.init()

    def __init__(self, app, route, request):
        self.app = app
        self.route = route
        self.request = request
        self._status = StatusCode('200 OK')
        self._aborted = False

        try:
            self.headers = ResponseHeaders(dict(app.get('default headers')))
        except KeyError, e:
            self.headers = ResponseHeaders()

        content_type = self.headers.get('Content-Type', None)

        if content_type:
            self._type = ContentType(content_type.value, True)
        else:
            self._type = ContentType('text/html; charset=utf-8', True)

        self._controller_class = (route.method.im_class
            if hasattr(route.method, 'im_class') else None)
        self._body = OutputBody(self, '')

        # Storage for request-specific local data
        self.locals = DotDict()

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        self._body.set(value)

    @property
    def status(self):
        '''
        The response status code. This is an instance of
        :class:`StatusCode <gimme.parsers.status.StatusCode>` and can be set
        using any of the following methods::

            response.status = 404
            response.status = "404 Not Found"
            reponse.status.set(404)

        Checking a status is as simple as doing any of the following::

            response.status == 404
            response.status == "404 Not Found"
        '''
        return self._status

    @status.setter
    def status(self, status):
        self._status.set(status)

    def _render(self, middleware=None):
        if self._controller_class:
            controller = self._controller_class(self.app, self.request, self)
            method = self.route.method
        else:
            controller = None
            def method():
                return self.route.method

        if middleware is None:
            middleware = (self.app._middleware + self.route.middleware)
        elif not middleware:
            middleware = []

        self.instantiated_middleware = self._instantiate_middleware(middleware)

        with nested(*self.instantiated_middleware):
            try:
                if not self._aborted:
                    self.body = method()
            except gimme.errors.AbortRender:
                self._aborted = method

    def _instantiate_middleware(self, middleware):
        result = []
        for i in middleware:
            result.append(i(self.app, self.request, self))
        return result

    def set(self, key, value):
        '''
        A shortcut for setting a response header.

        :param key: The key of the header to set.
        :param value: The value of the header.
        '''
        self.headers[key] = value
        return self

    def get(self, key):
        '''
        A shortcut for getting a response header.

        :param key: The key of the header to get.
        '''
        return self.headers[key]

    def redirect(self, path, code=302):
        '''
        A shortcut for setting the response status and HTTP "Location" header
        appropriately to redirect the requesting client.

        :param str path: The location to send the client to.
        :param code: The status code to set.
        '''
        self.status = code
        self.location = path

    @property
    def location(self):
        '''
        A shortcut for getting and setting the HTTP "Location" header.
        '''
        return self.get('Location')

    @location.setter
    def location(self, path):
        self.set('Location', path)

    @property
    def type(self):
        '''
        A shortcut for getting and setting the HTTP "Content-Type" header.
        '''
        return self._type

    @type.setter
    def type(self, content_type):
        self._type.set(content_type)

    def cookie(self, key, value, expires=None, http_only=False, secure=False,
            path='/', domain=None):
        '''
        A helper method for setting the HTTP "Set-Cookie" header.

        :param key: The key/name of the cookie.
        :param value: What to set the cookie to.
        :param expires: Number of seconds that the cookie should last before
            being expired. Defaults to ``None``, which makes the cookie
            last indefinitely.
        :param http_only: Set the HttpOnly flag.
        :param secure: Set the Secure flag.
        :param path: Limit the URI path that the cookie applies to.
        :param domain: Limit the domain that the cookie applies to.
        '''
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
        '''
        A helper method for expiring a previously-set cookie.

        :param key: The key/name of the cookie to expire.
        '''
        expires = datetime.datetime.fromtimestamp(0)
        self.cookie(key, 'deleted', expires=expires)

    def attachment(self, filename=None):
        '''
        A helper for setting the "Content-Disposition" and "Content-Type" HTTP
        headers for a given file. This makes it easy to pass a file to the
        client for downloading.

        Note, this is implemented as a setter-only property. In other words,
        you cannot "get" the attachment information with this property, but
        only set it.

        This is valid::

            response.attachment = "something.jpg"

        But this is **not**::

            print response.attachment
        '''
        if filename:
            self.headers['Content-Disposition'] = ('attachment; filename="%s"'
                % filename)
            mimetype, encoding = mimetypes.guess_type(filename)
            if mimetype:
                self.type = mimetype
        else:
            self.headers['Content-Disposition'] = 'attachment';

    attachment = property(None, attachment, None, attachment.__doc__)

    @property
    def charset(self):
        '''
        A helper for getting and setting the charset portion of the
        "Content-Type" header.
        '''
        return self._type.charset

    @charset.setter
    def charset(self, value):
        self._type.charset = value

    def links(self, links):
        '''
        A helper for setting the "Link" header. To set links, simply do
        something like::

            response.links = {
                'http://google.com/meta.rdf': 'meta'
            }

        Note that this is a setter-only property. Reading from it is not
        valid.
        '''
        buffer_ = []
        for k, v in links.iteritems():
            buffer_.append('<%s>; rel="%s"' % (v, k))
        self.headers['Link'] = ', '.join(buffer_)

    links = property(None, links, None, links.__doc__)

    def render(self, template, params):
        raise NotImplementedError("Response.render() not implemented!")

    def get_headers(self):
        headers = ResponseHeaders(self.headers)
        headers['Content-Type'] = str(self._type)
        return headers.items()

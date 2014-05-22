import types
from json import dumps as dump_json
from collections import namedtuple
from .parsers.contenttype import ContentType
import errors
import zlib


nt_format = namedtuple('nt_format', 'renderer content_type')


class BaseRenderer(object):
    def __eq__(self, content_type):
        return Format(self, content_type)

    def __repr__(self):
        return "<%s()>" % type(self).__name__


class BulkRenderer(list, BaseRenderer):
    def render(self, controller, data, request, response):
        for i in self:
            data = i.render(controller, data, request, response)
        return data

    def __repr__(self):
        return "<BulkRenderer([%s])>" % ', '.join(map(repr, self))


class Format(list, BaseRenderer):
    def __init__(self, renderer, content_type='*/*'):
        if not isinstance(content_type, ContentType):
            content_type = ContentType(content_type)
        self.append(nt_format(renderer, content_type))

    def __or__(self, other):
        if isinstance(other, Format):
            for i in other:
                self.append(nt_format(i.renderer, i.content_type))
        else:
            self.append(nt_format(other[0], other[1]))
        return self

    def __repr__(self):
        return "<Format[%s]>" % ', '.join(map(repr, self))

    @property
    def content_types(self):
        result = []
        for i in self:
            result.append(i.content_type)
        return result

    def get_by_content_type(self, content_type):
        for i in self:
            if i.content_type == content_type:
                return i.renderer
        raise IndexError("Could not find content_type: %s" % content_type)

    def render(self, controller, data, request, response):
        content_types = self.content_types
        try:
            priority = (request.accepted.filter(content_types)
                .get_highest_priority()).value
        except IndexError:
            priority = self[0].content_type
        renderer = self.get_by_content_type(priority)

        return renderer.render(controller, data, request, response)


class Template(BaseRenderer):
    def __init__(self, template_path):
        self.template_path = template_path

    def __repr__(self):
        return "<Template(%s)>" % self.template_path

    def render(self, controller, data, request, response):
        app = controller.app
        return app.engine.render(self.template_path, data)


class Json(BaseRenderer):
    def render(self, controller, data, request, response):
        response.type = 'application/json'
        return dump_json(data)


class Compress(BaseRenderer):
    def render(self, controller, data, request, response):
        if 'accept_encoding' in request.headers:
            if ('deflate' in
                    request.headers.accept_encoding.split(',')):
                try:
                    compressed = zlib.compress(data)
                except TypeError:
                    pass
                else:
                    response.headers['Content-Encoding'] = 'deflate'
                    response.headers['Content-Length'] = str(len(compressed))
                    return compressed
        return data

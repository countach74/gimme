import sys
import traceback
import types
from jinja2 import Environment, PackageLoader

from renderers import (
    BaseRenderer,
    Template,
    Json,
    Compress,
    Format,
    BulkRenderer
)


class MethodRenderer(list):
    def __init__(self, items=[]):
        if len(items) < 1 or not isinstance(items[0], ControllerMethod):
            raise ValueError("First argument to MethodRenderer must be "
                "an instance of ControllerMethod")

        self.im_class = items[0].im_class
        self.__name__ = items[0].__name__
        list.__init__(self, items)

    def __call__(self):
        controller = self[0].controller_instance
        data = self[0]()

        for i in self[1:]:
            data = i.render(controller, data)

        return data

    def __add__(self, other):
        if not isinstance(other, BaseRenderer):
            other = Template(other)
        self.append(other)
        return self

    def __repr__(self):
        return "<MethodRenderer([%s])>" % ', '.join(map(str, self))

    def __eq__(self, content_type):
        return Format(BulkRenderer(list(self[1:])), content_type)

    def template(self, template_path):
        self.append(Template(template_path))
        return self

    def json(self):
        self.append(Json())
        return self

    def compress(self):
        self.append(Compress())
        return self


class ControllerMethod(object):
    def __init__(self, cls, fn):
        self.im_class = cls
        self.fn = fn
        self.__name__ = fn.__name__

    def __call__(self):
        return self.fn(self.controller_instance)

    def __add__(self, other):
        if not isinstance(other, BaseRenderer):
            other = Template(other)
        return MethodRenderer([self, other])

    def __eq__(self, content_type):
        return Format(BulkRenderer([]), content_type)

    def template(self, template_path):
        return MethodRenderer([self, Template(template_path)])

    def json(self):
        return MethodRenderer([self, Json()])

    def compress(self):
        return MethodRenderer([self, Compress()])


class ControllerMeta(type):
    def __init__(mcs, name, bases, attrs):
        for key, value in [(k, v) for (k, v) in attrs.iteritems()
                if not k.startswith('_')]:
            if hasattr(value, '__call__'):
                setattr(mcs, key, ControllerMethod(mcs, value))

        type.__init__(mcs, name, bases, attrs)


class Controller(object):
    __metaclass__ = ControllerMeta

    def __init__(self, app, request, response):
        self.app = app
        self.request = request
        self.response = response

    def __new__(cls, *args):
        obj = object.__new__(cls, *args)

        for i in dir(obj):
            attr = getattr(obj, i)
            if isinstance(attr, ControllerMethod):
                attr.controller_instance = obj

        return obj


class ErrorController(Controller):
    def __init__(self, *args, **kwargs):
        Controller.__init__(self, *args, **kwargs)
        self.environment = Environment(
            loader=PackageLoader('gimme', 'templates'))

    def http404(self):
        self.response.status = 404

        return self.environment.get_template('errors/404.html').render({
            'headers': self.request.headers,
        })

    def http500(self):
        self.response.status = 500
        e_type, e_value, e_traceback = sys.exc_info()
        traceback.print_exception(e_type, e_value, e_traceback)

        return self.environment.get_template('errors/500.html').render({
            'message': "Oh snap! Something's borked. :(",
            'headers': self.request.headers,
            'traceback': traceback.format_exception(
                e_type,
                e_value,
                e_traceback)
        })

    def generic(self):
        return self.environment.get_template('errors/generic.html').render({
            'status': self.response._status
        })


class Poo(Controller):
    def poo(self):
        return {'this': 'is awesome!'}

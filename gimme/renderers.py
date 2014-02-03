import types
from json import dumps as dump_json
import errors


class ViewDecorator(object):
    def __new__(cls, fn=None):
        if isinstance(fn, ViewDecorator):
            obj = object.__new__(cls, fn)
            obj.__init__(fn)
            fn.modifiers.append(obj)
            return fn
        return object.__new__(cls, fn)

    def __init__(self, fn=None):
        self.fn = fn
        self.modifiers = [self]
        self.__name__ = fn.__name__

    def __get__(self, obj, cls=None):
        self._obj = obj
        self._cls = cls

        if not obj:
            return types.UnboundMethodType(self, None, cls)

        return types.MethodType(self, obj, cls)

    def __call__(self, *args, **kwargs):
        modifiers = self.modifiers
        fn = self.fn

        result = fn(*args, **kwargs)
        for modifier in modifiers:
            # Make sure we don't call modifiers twice
            if (modifier not in self.modifiers or
                    modifiers is self.modifiers):
                result = modifier.call(result)
        return result

    def call(self, result):
        pass

    @property
    def obj(self):
        try:
            return self._obj
        except AttributeError:
            return self.fn.obj

    @property
    def cls(self):
        try:
            return self._cls
        except AttributeError:
            return self.fn.cls

    @property
    def app(self):
        return self.obj.app

    @property
    def request(self):
        return self.obj.request

    @property
    def response(self):
        return self.obj.response

    def data(self):
        return self.fn(self.obj)


def view(template):
    class View(ViewDecorator):
        def call(self, body):
            return self.response.render(template, body)
    return View


def json():
    class Json(ViewDecorator):
        def call(self, body):
            self.response.headers['Content-Type'] = 'application/json'
            return dump_json(body)
    return Json


def format(type_):
    class Format(object):
        def __init__(self, fn):
            self.types = {
                type_: fn
            }
            self.fn = fn
            self.__name__ = fn.__name__

        def __get__(self, obj, cls=None):
            self.obj = obj
            self.cls = cls

            if not obj:
                return types.UnboundMethodType(self, None, cls)

            return types.MethodType(self, obj, cls)

        def __call__(self, *args, **kwargs):
            use_type = self.obj.request.accepted.filter(self.types.keys()).get_highest_priority()
            fn = self.types[str(use_type)] if use_type else self.fn
            fn._obj = self.obj

            return fn(*args, **kwargs)

        def call(self, body):
            return body

        def add_type(self, type_):
            def wrapper(fn):
                self.types[type_] = fn
                return self
            return wrapper

    return Format

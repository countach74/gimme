import types
from json import dumps as dump_json


class decorator(object):
    def __init__(self, fn):
        self.fn = fn
        self.__name__ = self.get_fn().__name__

    def __get__(self, instance, parent=None):
        if not instance:
            return types.UnboundMethodType(self, None, parent)

        self.get_fn().instance = instance
        self.get_fn().parent = parent
        return types.MethodType(self, instance, parent)

    def get_fn(self):
        fn = self.fn
        while hasattr(fn, 'fn'):
            fn = fn.fn
        return fn


def view(template):
    class wrapper(decorator):
        def __call__(self, *args, **kwargs):
            raw_output = self.fn(*args, **kwargs)
            return self.get_fn().instance.app.render(template, raw_output)

    return wrapper


def json():
    class wrapper(decorator):
        def __call__(self, *args, **kwargs):
            raw_output = self.fn(*args, **kwargs)
            self.get_fn().instance.response.set('Content-Type',
                'application/json')
            parsed_output = dump_json(raw_output)
            return parsed_output

    return wrapper


def format(content_type):
    formats = {}

    def make_wrapper(content_type):
        class wrapper(decorator):
            def __init__(self, fn):
                decorator.__init__(self, fn)
                formats[content_type] = self

            def __call__(self, *args, **kwargs):
                accepted = self.get_fn().instance.request.accepted
                priority_accept = accepted.get_highest_priority_for_mime(
                    formats.keys())

                if priority_accept:
                    method = formats[priority_accept]
                    self.get_fn().instance.response.set('Content-Type',
                        priority_accept)
                    result = method.fn(*args, **kwargs)
                    return result
                else:
                    return self.fn(*args, **kwargs)

            def add_type(self, content_type):
                return make_wrapper(content_type)

        return wrapper

    return make_wrapper(content_type)

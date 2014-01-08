import types
from json import dumps as dump_json


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
        self.formats = {}
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

        if self.formats:
            accepted = self.request.accepted
            priority_accept = accepted.get_highest_priority_for_mime(
                self.formats.keys())

            if priority_accept:
                fn = self.formats[priority_accept].fn
                modifiers = self.formats[priority_accept].modifiers

        result = fn(*args, **kwargs)
        for modifier in modifiers:
            result = modifier.call(result)
        return result

    def call(self, result):
        pass

    def add_format(self, content_type):
        cls = type(self)
        def wrapper(fn):
            self.formats[content_type] = cls(fn)
            return self
        return wrapper

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


def view(template=None):
    class View(ViewDecorator):
        def call(self, body):
            if template:
                return self.app.render(template, body)
            return body
    return View


def json():
    class Json(ViewDecorator):
        def call(self, body):
            self.response.headers['Content-Type'] = 'application/json'
            return dump_json(body)
    return Json


def format(content_type):
    formats = {}

    class Formatter(object):
      def __init__(self, content_type, fn):
        self.content_type = content_type
        self.fn = fn
        self.types = {}
        self.__name__ = fn.__name__

      def __get__(self, obj, cls):
        self._obj = obj
        self._cls = cls

        if obj:
          return types.MethodType(self, obj, cls)

        return self

      def __call__(self, *args, **kwargs):
        accepted = self._obj.request.accepted
        priority_accept = accepted.get_highest_priority_for_mime(
          self.types.keys())

        if priority_accept:
          fn = self.types[priority_accept]
          return fn(*args, **kwargs)

        return self.fn(*args, **kwargs)

      def add_type(self, content_type):
        def inner(fn):
          self.types[content_type] = fn
          return self
        return inner

      @property
      def im_class(self):
        return self._cls

    '''
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
    '''

    def wrapper(fn):
      return Formatter(content_type, fn)

    return wrapper


class View(object):
  def __init__(self, fn, template=None):
    self.fn = fn
    self.template = template
    self.formats = {}
    self.__name__ = fn.__name__

  def __get__(self, obj, cls):
    self.obj = obj
    self.cls = cls

    if obj:
      return types.MethodType(self, obj, cls)

    return self

  def view(self, template):
    self.template = template
    return self

  def json(self, *args, **kwargs):
    def inner(fn):
      self.obj.response.set('Content-Type', 'application/json')
      raw_output = fn(*args, **kwargs)
      return dump_json(raw_output)
    return inner

  def format(self, content_type, fn):
    self.formats[content_type] = fn
    return self

  def __call__(self, *args, **kwargs):
    print self.formats
    accepted = self.obj.request.accepted
    priority_accept = accepted.get_highest_priority_for_mime(
      self.formats.keys())

    if priority_accept:
      fn = self.formats[priority_accept]
      return fn(*args, **kwargs)

    return self.fn(*args, **kwargs)

  @property
  def im_class(self):
    return self.cls

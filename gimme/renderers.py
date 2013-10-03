import types
import json


class decorator(object):
  def __get__(self, instance, parent=None):
    self.instance = instance
    self.parent = parent
    return types.MethodType(self, instance)


def view(template):
  class wrapper(decorator):
    def __init__(self, fn):
      self.fn = fn

    def __call__(self, *args, **kwargs):
      raw_output = self.fn(*args, **kwargs)
      return self.instance.app.render(template, raw_output)

  return wrapper


def json():
  class wrapper(decorator):
    def __init__(self, fn):
      self.fn = fn

    def __call__(self, *args, **kwargs):
      raw_output = self.fn(*args, **kwargs)
      self.instance.response.set('Content-Type', 'application/json')
      return json.dumps(raw_output)

  return wrapper

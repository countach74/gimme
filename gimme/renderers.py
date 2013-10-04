import types
import json


class decorator(object):
  def __init__(self, fn):
    self.fn = fn
    self.__name__ = fn.__name__
    
  def __get__(self, instance, parent=None):
    if not instance:
      return types.UnboundMethodType(self, None, parent)
      
    self.instance = instance
    self.parent = parent
    return types.MethodType(self, instance, parent)


def view(template):
  class wrapper(decorator):
    def __call__(self, *args, **kwargs):
      raw_output = self.fn(*args, **kwargs)
      return self.instance.app.render(template, raw_output)

  return wrapper


def json():
  class wrapper(decorator):
    def __call__(self, *args, **kwargs):
      raw_output = self.fn(*args, **kwargs)
      self.instance.response.set('Content-Type', 'application/json')
      return json.dumps(raw_output)

  return wrapper


def test(param):
  print param
  class wrapper(decorator):
    def __call__(self, *args, **kwargs):
      data = self.fn(*args, **kwargs)
      print data
      return data
  return wrapper
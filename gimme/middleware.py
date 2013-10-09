import abc


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

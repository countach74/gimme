import abc
import re
import os
import random
from .dotdict import DotDict
from .ext.session import MemoryStore, Session as _Session


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


def static(path, expose_as=None):
  expose_as = (expose_as or os.path.basename(path)).strip('/')
  pattern = re.compile('^/%s.*' % re.escape(expose_as))

  import mimetypes
  mimetypes.init()

  class Static(Middleware):
    def enter(self):
      match = pattern.match(self.request.headers.path_info)
      self._file = None
      self._local_path = None

      if match:
        self._local_path = self._get_local_path(self.request.headers.path_info)
        if self._local_path:
          self.response.set('Content-Type', mimetypes.guess_type(self._local_path)[0])

    def exit(self):
      if self._local_path:
        self.response.status(200)
        try:
          with open(self._local_path, 'r') as f:
            self._serve(f)
        except OSError, e:
          pass

    def _serve(self, f):
      self.response.body = f.read()

    def _get_local_path(self, local_path):
      local_path = local_path.strip('/')[len(expose_as):].lstrip('/')
      temp_path = os.path.join(path, local_path)
      if temp_path.startswith(path) and os.path.exists(temp_path):
        return temp_path
      else:
        return None

  return Static


def cookie_parser():
  class CookieParser(Middleware):
    def enter(self):
      try:
        data = self.request.cookies.split('; ')
      except AttributeError:
        self.request.cookies = DotDict()
        return

      self.request.cookies = DotDict()
      for i in data:
        if i:
          split = i.split('=', 1)
          if split:
            self.request.cookies[split[0]] = split[1]

    def exit(self):
      pass

  return CookieParser


def session(store=MemoryStore, session_key='gimme_session'):
  storage = store()

  class Session(Middleware):
    def enter(self):
      self._new_session = False
      self.request.session = self._load_session()

    def exit(self):
      if self.request.session._state.is_dirty() or self._new_session:
        self.request.session.save()

    def _load_session(self):
      try:
        key = self.request.cookies[session_key]
      except KeyError:
        return self._create_session()

      try:
        return storage.get(key)
      except KeyError, e:
        return self._create_session()

    def _create_session(self):
      self._new_session = True
      key = self._make_session_key()
      self.response.set('Set-Cookie', '%s=%s' % (session_key, key))
      new_session = _Session(storage, key, {})
      storage.set(key, new_session)
      return new_session

    def _make_session_key(self, num_bits=256):
      return '%02x' % random.getrandbits(num_bits)

  return Session

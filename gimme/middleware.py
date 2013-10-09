import abc
import re
import os
import random
from .dotdict import DotDict
from .ext.sessionstores import MemoryStore


class Middleware(object):
  __metaclass__ = abc.ABCMeta

  def __enter__(self):
    self.enter()

  def __exit__(self, exc_type, exc_value, traceback):
    self.exc_type = exc_type
    self.exc_value = exc_value
    self.traceback = traceback
    self.exit()

  def _setup(self, app, request, response):
    self.app = app
    self.request = request
    self.response = response

  @abc.abstractmethod
  def enter(self):
    pass

  @abc.abstractmethod
  def exit(self):
    pass


class Static(Middleware):
  def __init__(self, path, expose_as=None):
    self.path = path
    self.expose_as = (expose_as or os.path.basename(path)).strip('/')
    self.pattern = re.compile('^/%s/.*' % re.escape(self.expose_as))

    import mimetypes
    mimetypes.init()
    self.mimetypes = mimetypes

  def enter(self):
    match = self.pattern.match(self.request.headers.path_info)
    self._file = None
    self.local_path = None

    if match:
      self.local_path = self._get_local_path(self.request.headers.path_info)
      if self.local_path:
        self.response.set('Content-Type', self.mimetypes.guess_type(self.local_path)[0])

  def exit(self):
    if self.local_path:
      try:
        with open(self.local_path, 'r') as f:
          self._serve(f)
      except OSError, e:
        pass

  def _serve(self, f):
    self.response.body = f.read()

  def _get_local_path(self, path):
    path = path.strip('/')[len(self.expose_as):].lstrip('/')
    local_path = os.path.join(self.path, path)
    if local_path.startswith(self.path) and os.path.exists(local_path):
      return local_path
    else:
      return None


class CookieParser(Middleware):
  def enter(self):
    data = self.request.cookies.split('; ')
    self.request.cookies = DotDict()
    for i in data:
      if i:
        split = i.split('=', 1)
        if split:
          self.request.cookies[split[0]] = split[1]

  def exit(self):
    print self.request.cookies


class Session(Middleware):
  def __init__(self, store=MemoryStore, key='gimme_session'):
    if hasattr(store, '__init__'):
      store = store()
    self._store = store
    self._key = key

  def enter(self):
    self.request.session = self._load_session()

  def exit(self):
    self._store.set(

  def _load_session(self):
    try:
      cookie = self.request.cookies[self._key]
    except KeyError:
      return self._create_session()

    return self._store.get(cookie)

  def _create_session(self):
    key = self._make_session_key()
    self.request.session[self._key] = key
    self.response.set('Set-Cookie', self._key, key)
    return {}

  def _make_session_key(self, num_bits=256):
    return '%02x' % random.getrandbits(num_bits)

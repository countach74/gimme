import abc


class BaseStore(object):
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def get(self, key):
    pass

  @abc.abstractmethod
  def set(self, key, value):
    pass


class MemoryStore(BaseStore):
  def __init__(self):
    self._sessions = {}

  def __repr__(self):
    return "MemoryStore(%s)" % ', '.join(self._sessions.keys())

  def get(self, key):
    return self._sessions[key]

  def set(self, key, value):
    self._sessions[key] = value


class ChangeTracker(object):
  def __init__(self):
    self._dirty = False

  def is_dirty(self):
    return self._dirty

  def dirty(self):
    self._dirty = True

  def clean(self):
    self._dirty = False


class NotifiedMixin(object):
  def __init__(self):
    if isinstance(self, list):
      i = 0
      for item in self:
        self[i] = self._check(item)
        i += 1
    elif isinstance(self, dict):
      for k, v in self.items():
        self[k] = self._check(v)

  def _check(self, item):
    if isinstance(item, dict) and not isinstance(item, NotifiedDict):
      item = NotifiedDict(self._state, item)
    if isinstance(item, list) and not isinstance(item, NotifiedList):
      item = NotifiedList(self._state, item)
    return item


class NotifiedDict(dict, NotifiedMixin):
  def __init__(self, state, *args, **kwargs):
    self._state = state
    dict.__init__(self, *args, **kwargs)
    NotifiedMixin.__init__(self)

  def __setitem__(self, key, value):
    self._state.dirty()
    value = self._check(value)
    dict.__setitem__(self, key, value)

  def __delitem__(self, key):
    self._state.dirty()
    dict.__delitem__(self, key)


class NotifiedList(list, NotifiedMixin):
  def __init__(self, state, *args, **kwargs):
    self._state = state
    list.__init__(self, *args, **kwargs)
    NotifiedMixin.__init__(self)

  def __delitem__(self, key):
    self._state.dirty()
    list.__delitem__(self, key)

  def append(self, item):
    self._state.dirty()
    item = self._check(item)
    list.append(self, item)

  def remove(self, item):
    self._state.dirty()
    list.remove(self, item)

  def insert(self, index, item):
    self._state.dirty()
    item = self._check(item)
    list.insert(self, index, item)

  def pop(self, *args, **kwargs):
    self._state.dirty()
    return list.pop(self, *args, **kwargs)


class Session(object):
  def __init__(self, store, key, data={}):
    self._store = store
    self._key = key
    self._state = ChangeTracker()
    self._data = NotifiedDict(self._state, data)

  def save(self):
    if self._state.is_dirty():
      self._store.set(self._key, self._data)

  def __getitem__(self, key):
    return self._data[key]

  def __setitem__(self, key, value):
    self._data[key] = value

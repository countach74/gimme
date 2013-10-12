from urlparse import parse_qs


class QueryString(object):
  _reserved_attrs = ('_query_string', '_parsed')

  def __init__(self, query_string):
    self._query_string = query_string
    self._parsed = parse_qs(query_string)

  def __repr__(self):
    return 'QueryString(%s)' % self._parsed

  def __getattr__(self, key):
    if key not in QueryString._reserved_attrs:
      try:
        value = self._parsed[key]
      except KeyError, e:
        raise AttributeError(key)
      return value if len(value) > 1 else value[0]
    else:
      return object.__getattr__(self, key)

  def __setattr__(self, key, value):
    if key not in QueryString._reserved_attrs:
      if key not in self._parsed:
        self._parsed[key] = []
      self._parsed[key].append(value)
    else:
      return object.__setattr__(self, key, value)
    return object.__setattr__(self, key, value)

  def __getitem__(self, key):
    try:
      return self.__getattr__(key)
    except AttributeError:
      raise KeyError(key)

  def __setitem__(self, key, value):
    self.__setattr__(key, value)

  def __delitem__(self, key):
    del(self._parsed[key])

  def __contains__(self, key):
    return key in self._parsed

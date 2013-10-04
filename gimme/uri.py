from urlparse import parse_qs


class QueryString(object):
  _reserved_attrs = ('_query_string', '_parsed')

  def __init__(self, query_string):
    self._query_string = query_string
    self._parsed = parse_qs(query_string)

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

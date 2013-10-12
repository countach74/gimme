import re
from .headers import RequestHeaders
from .dotdict import DotDict
from .uri import QueryString
from .errors import AcceptFormatError


class AcceptFormat(object):
  _pattern = re.compile('(?P<type>[a-zA-Z0-9\-_\*]+)/(?P<subtype>'
    '[a-zA-Z0-9\-_\*]+)(?:;q=(?P<priority>[0-9]*[\.]?[0-9]*))?')
  _mime_pattern = re.compile('(?P<type>[a-zA-Z0-9\-_\*]+)/'
    '(?P<subtype>[a-zA-Z0-9\-_\*]+)')

  def __init__(self, data):
    self._data = data
    self._match = self._pattern.match(data)
    if not self._match:
      raise AcceptFormatError("Invalid accept format")
    else:
      groups = self._match.groupdict()
      self.type = groups['type']
      self.subtype = groups['subtype']
      self.priority = (
        float(groups['priority']) if groups['priority'] is not None else 1)

  def __repr__(self):
    return "<AcceptFormat(%s/%s, priority %s)>" % (
      self.type, self.subtype, self.priority)

  def __str__(self):
    return '%s/%s' % (self.type, self.subtype)

  def test(self, mime):
    if self.type == '*':
      return True

    match = self._mime_pattern.match(mime)
    if match:
      data = match.groupdict()

      if data['type'] == self.type and data['subtype'] == self.subtype:
        return True
      elif self.subtype == '*':
        return True
    return False


class AcceptedList(object):
  def __init__(self, raw):
    self._raw = raw
    self._data = list(self._parse(raw))

  def _parse(self, raw):
    split = raw.split(',')
    for i in split:
      try:
        yield AcceptFormat(i)
      except AcceptFormatError:
        continue

  def get_items_by_priority(self):
    return sorted(self._data, key=lambda x: x.priority, reverse=True)

  def get_highest_priority(self):
    try:
      return self.get_items_by_priority()[0]
    except IndexError:
      return None

  def get_highest_priority_for_mime(self, mime):
    candidates = []

    if not isinstance(mime, list):
      mime = [mime]

    for i in self.get_items_by_priority():
      for j in mime:
        if i.test(j):
          candidates.append(j)

    return candidates[0] if len(candidates) else None

  def __repr__(self):
    return str(self._data)


class Request(object):
  def __init__(self, app, environ, match=None):
    self.app = app
    self.environ = environ
    self.match = match
    self.headers = RequestHeaders()
    self.wsgi = RequestHeaders()
    self.params = DotDict(match.match.groupdict() if match else {})

    self._populate_headers(environ)

    self.query = QueryString(self.headers.query_string
      if 'query_string' in self.headers else '')

    self.accepted = AcceptedList(self.headers.accept if 'accept' in
      self.headers else None)

    self.cookies = self.headers.cookie if 'cookie' in self.headers else ''

  def _populate_headers(self, environ):
    for k, v in environ.iteritems():
      key = k.lower()
      if key.startswith('http_'):
        self.headers[key[5:]] = v
      elif key.startswith('wsgi.'):
        self.wsgi[key[5:]] = v
      else:
        self.headers[key] = v

  def get(self, key):
    return self.headers[key.replace('-', '_')]

  def accepts(self, content_type):
    return content_type in self.accepted

import re


class ContentType(object):
    _pattern = re.compile('(?P<category>[a-zA-Z0-9_\-]+|\*)?/?(?P<type>[a-zA-Z0-9_\-]+|\*)(?:;\s*charset=)?(?P<charset>[a-zA-Z0-9_\-]+)?')

    def __init__(self, content_type, use_encoding=False):
        self._content_type = content_type
        self._use_encoding = use_encoding
        self.charset = 'utf-8'
        self.set(content_type)

    def set(self, content_type):
        self._match = self._pattern.search(content_type)

        if not self._match:
            self._category = ''
            self._type = ''
            self.charset = 'utf-8'

        else:
            self._groups = self._match.groupdict()

            # Some helpers to make accessing data easier
            self._category = self._groups['category']
            self._type = self._groups['type']
            if self._groups['charset']:
                self.charset = self._groups['charset']

    def get(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, ContentType):
            try:
                other = ContentType(other)
            except ValueError:
                return False

        if other._category is None or self._category is None:
            return (other._type == self._type
                or other._type == '*'
                or self._type == '*')
        elif (other._category == self._category
                or self._category == '*'
                or other._category == '*'):
            if (other._type == '*' or self._type == '*') or (
                    other._type == self._type):
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        if self._category is None:
            return '<ContentType(%s)>' % self._type
        elif self._use_encoding:
            return '<ContentType(%s/%s; charset=%s)>' % (
                self._category, self._type, self.charset)
        else:
            return '<ContentType(%s/%s)>' % (self._category, self._type)

    def __str__(self):
        if self._category is None:
            return self._type
        elif self._use_encoding:
            return '%s/%s; charset=%s' % (self._category, self._type,
                self.charset)
        else:
            return '%s/%s' % (self._category, self._type)

    def __unicode__(self):
        return unicode(str(self))

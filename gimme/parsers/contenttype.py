import re


class ContentType(object):
    _pattern = re.compile('^(?:(?P<category>[a-zA-Z0-9_\-]+|\*)/)?(?P<type>[a-zA-Z0-9_\-]+|\*).*')

    def __init__(self, content_type):
        self._content_type = content_type
        self._match = self._pattern.match(content_type)

        if not self._match:
            #raise ValueError("Invalid Content-Type: %s" % content_type)
            self._category = ''
            self._type = ''

        else:
            self._groups = self._match.groupdict()

            # Some helpers to make accessing data easier
            self._category = self._groups['category']
            self._type = self._groups['type']

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
        else:
            return '<ContentType(%s/%s)>' % (self._category, self._type)

    def __str__(self):
        if self._category is None:
            return self._type
        else:
            return '%s/%s' % (self._category, self._type)

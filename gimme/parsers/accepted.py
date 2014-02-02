import re


class AcceptedParser(object):
    _pattern = re.compile('(?P<value>[^;]+)(?:\s*;\s*q\s*=\s*'
        '(?P<priority>[0-9]*\.?[0-9]*))?')

    def __init__(self, data, value_parser=None):
        self._data = data
        self._value_parser = value_parser
        self._match = self._pattern.match(data)

        if not self._match:
            raise ValueError("Invalid accept type.")

        temp = self._match.groupdict()

        self.value = (
            temp['value'] if not value_parser
            else value_parser(temp['value'])
        )

        self.priority = (
            float(temp['priority'])
            if temp['priority'] is not None else 1
        )

    def __eq__(self, other):
        if isinstance(other, AcceptedParser):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return self.priority > other.priority

    def __lt__(self, other):
        return not self.__gt__(other)

    def __repr__(self):
        return "<AcceptedParser(%s, %s)>" % (self.value, self.priority)

    def __str__(self):
        return str(self.value)


class AcceptedList(list):
    _separator = re.compile('\s*,\s*')

    def __repr__(self):
        return '<AcceptedList(%s)>' % ', '.join(map(str, self))

    def __contains__(self, obj):
        for i in self:
            if i.value == obj:
                return True
        return False

    def filter(self, value):
        return type(self)([i for i in self if i.value == value])

    def get_by_priority(self):
        return type(self)(sorted(self, reverse=True))

    def get_highest_priority(self):
        return self.get_by_priority()[0]
            
    @classmethod
    def parse(cls, data, value_parser=None):
        result = []
        split = cls._separator.split(data)
        for i in split:
            try:
                result.append(AcceptedParser(i, value_parser))
            except ValueError:
                continue
        return cls(result)

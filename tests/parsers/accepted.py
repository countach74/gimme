import unittest
from gimme.parsers.accepted import AcceptedList, AcceptedParser
from gimme.parsers.contenttype import ContentType


class AcceptedParserTest(unittest.TestCase):
    def setUp(self):
        self.parser1 = AcceptedParser('application/json;q=0.9', ContentType)
        self.parser2 = AcceptedParser('application/json;q=0.8')

    def test_eq(self):
        assert self.parser1 == 'json'
        assert self.parser2 == 'application/json'

    def test_ne(self):
        assert self.parser1 != 'html'
        assert self.parser2 != 'application/stuff'

        assert not self.parser1 != 'json'
        assert not self.parser2 != 'application/json'

    def test_gt(self):
        assert self.parser1 > self.parser2
        assert not self.parser2 > self.parser1

    def test_lt(self):
        assert self.parser2 < self.parser1
        assert not self.parser1 < self.parser2

    def test_str(self):
        assert str(self.parser1) == 'application/json'


class AcceptedListTest(unittest.TestCase):
    def setUp(self):
        self.accepted = AcceptedList.parse(
            'text/html ;q=0.8,application/json;q=0.5,text/plain; q=1',
            ContentType)

    def test_filter(self):
        filtered = self.accepted.filter('html')
        assert len(filtered) == 1 and filtered[0] == 'text/html'

    def test_get_by_priority(self):
        assert self.accepted.get_by_priority()[0].priority == 1

    def test_get_highest_priority(self):
        assert self.accepted.get_highest_priority() == 'text/plain'

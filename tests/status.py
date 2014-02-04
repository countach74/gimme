import unittest
from gimme.status import StatusCode


class StatusCodeTest(unittest.TestCase):
    def setUp(self):
        self.status1 = StatusCode(404)
        self.status2 = StatusCode('500 Internal Server Error')

    def test_code(self):
        assert self.status1.code == 404
        assert self.status2.code == 500

    def test_text(self):
        assert self.status1.text == 'Not Found'
        assert self.status2.text == 'Internal Server Error'

    def test_get(self):
        assert self.status1.get() == '404 Not Found'
        assert self.status2.get() == '500 Internal Server Error'

    def test_set(self):
        self.status1.set(401)
        self.status2.set('100 Continue')
        assert self.status1.get() == '401 Not Authorized'
        assert self.status2.get() == '100 Continue'
        assert self.status1.code == 401
        assert self.status2.code == 100
        assert self.status1.text == 'Not Authorized'
        assert self.status2.text == 'Continue'

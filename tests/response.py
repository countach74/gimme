import unittest
import gimme
import datetime
from . import test_helpers


class ResponseTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

        body = '{"test": "data"}'

        self.response = gimme.Response(200, {
            'http_content_type': 'application/json',
            'http_content_length': str(len(body)),
            'http_x_requested_with': 'XMLHttpRequest',
            'http_cookie': 'cookie_test=some_cookie_to_delete'
        })

    def test_set_get(self):
        self.response.set('Content-Type', 'text/plain')
        assert self.response.get('Content-Type') == 'text/plain'

    def test_location(self):
        self.response.redirect('/somewhere_else')
        assert self.response.status.code == 302
        assert self.response.get('Location') == '/somewhere_else'

    def test_type(self):
        self.response.type = 'application/pdf'
        assert self.response.type == 'application/pdf'

    def test_cookie(self):
        self.response.cookie('simple_cookie', 'some_data')
        assert self.response.headers['Set-Cookie'] == 'simple_cookie=some_data; Path=/'

        self.response.cookie('complex_cookie', 'more_data', path='/somewhere',
            domain='something.test.com', expires=360000)
        # Add assert to test cookie

    def test_clear_cookie(self):
        self.response.clear_cookie('cookie_test')
        assert self.response.headers['Set-Cookie'] == (
            'cookie_test=deleted; Path=/; Expires=Wed, 31 Dec 1969 16:00:00 GMT')

    def test_status(self):
        self.response.status = 401
        assert self.response.status.code == 401
        assert self.response.status.text == 'Not Authorized'

    def test_attachment(self):
        self.response.attachment = 'file.jpg'
        assert self.response.headers['Content-Disposition'] == ('attachment; '
            'filename="file.jpg"')
        assert self.response.type == 'image/jpeg'

    def test_charset(self):
        self.response.charset = 'UTF-8'
        assert self.response.charset == 'UTF-8'
        self.response.charset = 'ASCII'
        assert self.response.charset == 'ASCII'

    def test_links(self):
        self.response.links = {
            'next': 'http://google.com',
            'prev': 'http://apple.com'
        }
        assert self.response.headers['Link'] == (
            '<http://apple.com>; rel="prev", '
            '<http://google.com>; rel="next"')

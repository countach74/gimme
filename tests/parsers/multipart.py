import unittest
import tempfile
import mmap
import sys
import os
from gimme.parsers.multipart import (
    MultipartParser,
    MultipartHeaders,
    MultipartFile,
    MMapChunk)


BOUNDARY = '---------------------------41184676334'


class MultipartHeadersTest(unittest.TestCase):
    def setUp(self):
        self.raw_headers = '''
Content-Disposition: form-data; name="file"; filename="some_file.jpg"
Content-Type: image/jpeg
'''.replace('\n', '\r\n')
        self.headers = MultipartHeaders(self.raw_headers)

    def test_get(self):
        assert self.headers.get('Content-Type', '') == 'image/jpeg'
        assert self.headers.get('content-Type', '') == 'image/jpeg'
        assert self.headers.get('Not-Here', 'blah') == 'blah'
        assert self.headers.get('not-here', 'blah') == 'blah'

    def test_getitem(self):
        assert self.headers['Content-Type'] == 'image/jpeg'
        assert self.headers['content-type'] == 'image/jpeg'

    def test_setitem(self):
        self.headers['Something-New'] = 'a new thing'
        assert self.headers['Something-New'] == 'a new thing'
        assert self.headers['something-new'] == 'a new thing'


class MultipartFileTest(unittest.TestCase):
    def setUp(self):
        self.raw_data = '''
-----------------------------41184676334
Content-Disposition: form-data; name="image1"; filename="GrandCanyon.jpg"
Content-Type: image/jpeg


blah data here
'''.replace('\n', '\r\n')

        self.tempfile = tempfile.NamedTemporaryFile()
        self.tempfile.write(self.raw_data)
        self.tempfile.seek(0)
        self.mmap = mmap.mmap(self.tempfile.fileno(), 0)
        self.multipart_file = MultipartFile(BOUNDARY, self.mmap, 0,
            len(self.raw_data))

    def test_filename(self):
        assert self.multipart_file.filename == 'GrandCanyon.jpg'

    def test_disposition(self):
        assert self.multipart_file.disposition == 'form-data'

    def test_content_type(self):
        assert self.multipart_file.content_type == 'image/jpeg'

    def test_file_read(self):
        assert self.multipart_file.file.read() == 'blah data here'


class MultipartParserTest(unittest.TestCase):
    def setUp(self):
        self.raw_data = '''
-----------------------------41184676334
Content-Disposition: form-data; name="caption"

Summer vacation
-----------------------------41184676334
Content-Disposition: form-data; name="image1"; filename="GrandCanyon.jpg"
Content-Type: image/jpeg

Some binary data
-----------------------------41184676334--
'''.replace('\n', '\r\n')

        self.tempfile = tempfile.NamedTemporaryFile()
        self.tempfile.write(self.raw_data)
        self.tempfile.seek(0)
        self.multipart_parser = MultipartParser(BOUNDARY, self.tempfile)

    def test_keys(self):
        assert self.multipart_parser.keys() == ['caption', 'image1']

    def test_value(self):
        assert self.multipart_parser['caption'].value == 'Summer vacation'

    def test_file_read(self):
        assert self.multipart_parser['image1'].file.read() == 'Some binary data'


class MMapChunkTest(unittest.TestCase):
    def setUp(self):
        self.file = tempfile.NamedTemporaryFile()
        self.file.write('''\
line 1
line 2
does this work?''')
        self.file.seek(0)
        self.mmap = mmap.mmap(self.file.fileno(), 0)
        self.chunk = MMapChunk(self.mmap, 5, 20)

    def test_read(self):
        assert self.chunk.read() == '1\nline 2\ndoes t'
        self.chunk.seek(2)
        assert self.chunk.read(3) == 'lin'

    def test_seek(self):
        self.chunk.seek(1)
        assert self.chunk.read(1) == '\n'
        self.chunk.seek(1, os.SEEK_CUR)
        assert self.chunk.read(1) == 'i'
        self.chunk.seek(1, os.SEEK_END)
        assert self.chunk.read(1) == 't'

    def test_readline(self):
        assert self.chunk.readline() == '1\n'
        assert self.chunk.tell() == 2

    def test_readlines(self):
        assert self.chunk.readlines() == [
            '1\n',
            'line 2\n',
            'does t'
        ]

    def test_size(self):
        assert self.chunk.size() == 15

    def test_tell(self):
        assert self.chunk.tell() == 0
        self.chunk.seek(5)
        assert self.chunk.tell() == 5

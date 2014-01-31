import re
import mmap
import mimetools
from tempfile import NamedTemporaryFile
import sys
from ..errors import MultipartError


class MultipartHeaders(dict):
    _pattern = re.compile('^([a-zA-Z0-9_\-]+):\s*(.*?)$', re.M)

    def __init__(self, raw_headers):
        self._raw_headers = raw_headers
        self._parse()

    def _parse(self):
        headers = self._pattern.findall(self._raw_headers)
        for key, value in headers:
            self[key] = value.strip()

    def get(self, key, default=None):
        return dict.get(self, key.lower(), default)

    def __getitem__(self, key):
        return dict.__getitem__(self, key.lower())

    def __setitem__(self, key, value):
        return dict.__setitem__(self, key.lower(), value)

    def __delitem__(self, key):
        return dict.__delitem__(self, key.lower())


class MultipartFile(object):
    _headers_pattern = re.compile('^(.*?)\r\n\r\n', re.S | re.M)
    _name_pattern = re.compile('''name=(?P<quote>["'])(.*?)(?P=quote);?''')
    _filename_pattern = re.compile('''filename=(?P<quote>["'])(.*?)(?P=quote);?''')
    _disposition_pattern = re.compile('^([a-zA-Z0-9_\-]+)')

    def __init__(self, boundary, data, pos, endpos):
        self._boundary = boundary
        self._data = data
        self._pos = pos
        self._endpos = endpos
        self.headers, self._headers_length = self._get_headers()
        self.disposition = self._get_disposition()
        
        # Before continuing, check disposition is sane
        if self.disposition not in ('form-data', 'file'):
            raise MultipartError("Invalid disposition type: %s" %
                self.disposition)
        
        self.name = self._get_field_name()
        self.filename = self._get_field_filename()
        self.content_type = self.headers.get('content-type', None)
        self.file = self._make_tempfile()
        
        if self.disposition == 'form-data' and self.content_type is None:
            self.value = self.file.read()
            self.file.seek(0)
        else:
            self.value = None

    def __repr__(self):
        return '<MultipartFile(%s)>' % self.name
        
    def _get_disposition(self):
        disposition = self.headers.get('content-disposition', '')
        match = self._disposition_pattern.search(disposition)
        if match:
            return match.group(1)

    def _get_field_name(self):
        disposition = self.headers.get('content-disposition', '')
        match = self._name_pattern.search(disposition)
        if not match:
            raise MultipartError("Multipart file missing (or invalid) name in "
                "content-disposition")
        return match.group(2)

    def _get_field_filename(self):
        disposition = self.headers.get('content-disposition', '')
        match = self._filename_pattern.search(disposition)
        if match:
            return match.group(2)

    def _make_tempfile(self):
        transfer_encoding = self.headers.get('content-transfer-encoding',
            '').lower()
        tf = NamedTemporaryFile()
        start_pos = self._pos + self._headers_length + 2
        file_length = (self._endpos - 2) - start_pos
        bytes_read = 0

        self._data.seek(start_pos)

        while bytes_read < file_length:
            remaining_bytes = (self._endpos - 2) - self._data.tell()
            chunk_size = min(8196, remaining_bytes)
            tf.write(self._data.read(chunk_size))
            bytes_read += chunk_size

        tf.seek(0)

        if transfer_encoding not in ('', '7bit', '8bit', 'binary'):
            decoded_tf = NamedTemporaryFile()
            mimetools.decode(tf, decoded_tf, transfer_encoding)
            decoded_tf.seek(0)
            return decoded_tf
        else:
            return tf

    def _get_headers(self):
        match = self._headers_pattern.search(self._data, self._pos,
            self._endpos)
        if not match:
            raise MultipartError("Invalid multipart headers.")
        raw_headers = self._data[match.start():min(match.end(), 8196)]
        return MultipartHeaders(raw_headers), len(raw_headers)


class MultipartParser(dict):
    def __init__(self, boundary, fileobj, chunk_size=8096):
        self.boundary = boundary
        self.fileobj = fileobj
        self.chunk_size = chunk_size
        dict.__init__(self, self._parse())

    def _split_files(self):
        files = []
        self.fileobj.seek(0)

        pattern = re.compile('(?<=--{0})(.*?)(?=--{0})'.format(
            re.escape(self.boundary)), re.S)
        filedata = mmap.mmap(self.fileobj.fileno(), 0)

        for i in pattern.finditer(filedata):
            try:
                files.append(MultipartFile(self.boundary, filedata, i.start(),
                    i.end()))
            except MultipartError:
                continue

        filedata.close()

        return files

    def _parse(self):
        for i in self._split_files():
            yield i.name, i

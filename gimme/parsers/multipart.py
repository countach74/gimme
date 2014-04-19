import re
import mmap
import mimetools
import codecs
from tempfile import NamedTemporaryFile
import sys
import os
from .. import errors


class MMapChunk(object):
    def __init__(self, mmap_file, start_pos, end_pos):
        self._file = mmap_file
        self._start_pos = start_pos
        self._end_pos = end_pos
        self._pos = start_pos

    def __repr__(self):
        return "<MMapChunk(%s)>" % self._file

    def close(self):
        pass

    def flush(self):
        self._file.flush(self._start_pos, self.size())

    def read(self, size=0):
        if size:
            data = self._file[self._pos:min(self._pos + size, self._end_pos)]
            self._pos = min(self._pos + size, self._end_pos)
        else:
            data = self._file[self._pos:self._end_pos]
            self._pos = self._end_pos
        return data

    def readline(self, size=0):
        line = self._file.readline()
        length = len(line)
        original_pos = self._pos

        if self._pos + length > self._end_pos:
            line = line[0:self._end_pos - self._pos]
            self._pos = self._end_pos
            length = len(line)
        else:
            self._pos = self._pos + length

        if size > 0 and length > size:
            line = line[0:size]
            self._pos = original_pos + size
            length = len(line)

        # Some hackery to chomp off the first characters of mmap's readline(),
        # if they happen to come before the MMapChunk's start_pos
        temp_start = self._file.tell() - self._start_pos

        if temp_start < self.tell():
            line = line[self.tell()-temp_start:]
            self._pos = self._pos - (self.tell() - temp_start)

        return line

    def readlines(self):
        lines = []
        data = self.readline()
        while data:
            lines.append(data)
            data = self.readline()
        return lines

    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            self._pos = min(self._start_pos + offset, self._end_pos)
        elif whence == os.SEEK_CUR:
            self._pos = min(self._pos + offset, self._end_pos)
        elif whence == os.SEEK_END:
            self._pos = max(self._end_pos - offset, self._start_pos)
        else:
            raise Exception("Invalid seek whence: %s" % whence)

    def size(self):
        return self._end_pos - self._start_pos

    def tell(self):
        return self._pos - self._start_pos


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
    _content_type_pattern = re.compile('^(?P<content_type>[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+)(?:;\s*charset=)?(?P<charset>[a-zA-Z0-9_\-]+)?')

    def __init__(self, boundary, data, pos, endpos):
        self._boundary = boundary
        self._data = data
        self._pos = pos
        self._endpos = endpos
        self.headers, self._headers_length = self._get_headers()
        self.disposition = self._get_disposition()
        
        # Before continuing, check disposition is sane
        if self.disposition not in ('form-data', 'file'):
            raise errors.MultipartError("Invalid disposition type: %s" %
                self.disposition)
        
        self.name = self._get_field_name()
        self.filename = self._get_field_filename()
        self.content_type, self.charset = self._get_type()
        self.file = self._make_file()
        
        if self.disposition == 'form-data' and self.content_type is None:
            self.value = self.file.read().decode(self.charset)
            self.file.seek(0)
        else:
            self.value = None

    def __repr__(self):
        return '<MultipartFile(%s)>' % self.name

    def _get_type(self):
        temp = self.headers.get('content-type', None)

        if not temp:
            return (None, 'ISO-8859-1')

        match = self._content_type_pattern.search(temp)
        if match:
            groups = match.groupdict()
            return (groups['content_type'], groups.get('charset',
                'ISO-8859-1'))
        else:
            return ('text/plain', 'ISO-8859-1')

    def _get_disposition(self):
        disposition = self.headers.get('content-disposition', '')
        match = self._disposition_pattern.search(disposition)
        if match:
            return match.group(1)

    def _get_field_name(self):
        disposition = self.headers.get('content-disposition', '')
        match = self._name_pattern.search(disposition)
        if not match:
            raise errors.MultipartError("Multipart file missing (or invalid) name in "
                "content-disposition")
        return match.group(2)

    def _get_field_filename(self):
        disposition = self.headers.get('content-disposition', '')
        match = self._filename_pattern.search(disposition)
        if match:
            return match.group(2)

    def _make_file(self):
        start_pos = self._pos + self._headers_length + 2
        chunkfile = MMapChunk(self._data, start_pos, self._endpos - 2)
        transfer_encoding = self.headers.get('content-transfer-encoding',
            '').lower()
        if transfer_encoding not in ('', '7bit', '8bit', 'binary'):
            try:
                chunkfile = codecs.getreader(transfer_encoding)(chunkfile)
            except (TypeError, LookupError):
                pass
        try:
            return codecs.getreader(self.charset)(chunkfile)
        except (TypeError, LookupError):
            return chunkfile

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
            try:
                return codecs.getreader(self.charset)(decoded_tf)
            except (TypeError, LookupError):
                return decoded_tf
        else:
            try:
                return codecs.getreader(self.charset)(tf)
            except (TypeError, LookupError):
                return tf

    def _get_headers(self):
        match = self._headers_pattern.search(self._data, self._pos,
            self._endpos)
        if not match:
            raise errors.MultipartError("Invalid multipart headers.")
        raw_headers = self._data[match.start():min(match.end(), 8196)]
        return MultipartHeaders(raw_headers), len(raw_headers)

    def _cleanup(self):
        self.file.close()


class MultipartParser(dict):
    def __init__(self, boundary, fileobj, chunk_size=8096):
        self.boundary = boundary
        self.fileobj = fileobj
        self.chunk_size = chunk_size
        self.tempfile = self._make_tempfile(fileobj)
        dict.__init__(self, self._parse())

    def _make_tempfile(self, fileobj):
        tf = NamedTemporaryFile()
        chunk = fileobj.read(self.chunk_size)
        while chunk:
            tf.write(chunk)
            chunk = fileobj.read(self.chunk_size)
        tf.seek(0)
        return tf

    def _split_files(self):
        files = []
        #self.fileobj.seek(0)

        pattern = re.compile('(?<=--{0})(.*?)(?=--{0})'.format(
            re.escape(self.boundary)), re.S)
        self.filedata = mmap.mmap(self.tempfile.fileno(), 0)

        for i in pattern.finditer(self.filedata):
            try:
                files.append(MultipartFile(self.boundary, self.filedata, i.start(),
                    i.end()))
            except errors.MultipartError:
                continue

        return files

    def _cleanup(self):
        for i in self.itervalues():
            i._cleanup()
        self.tempfile.close()
        self.filedata.close()

    def _parse(self):
        for i in self._split_files():
            yield i.name, i

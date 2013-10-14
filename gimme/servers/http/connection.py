import os
import sys
import datetime
import socket
from StringIO import StringIO
from .headers import RequestHeaders, RequestLine
from ...errors import FDError
from ...dotdict import DotDict


def parse_body(request):
    try:
        return request.split('\r\n\r\n', 1)[1]
    except IndexError:
        return ''


def populate_format_data(connection, response_length, environ):
    now = datetime.datetime.now()
    timestamp = now.strftime("%d %b %Y %H:%M:%S")

    try:
        status_code, status_message = connection.status.split(None, 1)
    except ValueError:
        status_code = 'INVALID'
        status_message = 'INVALID'

    if 'http_user_agent' in environ:
        user_agent = environ.http_user_agent
    else:
        user_agent = '-'

    if 'referer' in environ:
        referer = environ.referer
    else:
        referer = '-'

    return {
        'remote_host': environ.remote_addr if (
            'remote_addr' in environ else '-'),
        'timestamp': timestamp,
        'request_line': "%s %s %s" % (
            environ.request_method if 'request_method' in environ else '-',
            environ.request_uri if 'request_uri' in environ else '-',
            environ.server_protocol if 'server_protocol' in environ else '-'),
        'status_code': status_code,
        'body_size': response_length,
        'local_address': environ.server_addr if (
            'server_addr' in environ else '-'),
        'environment': environ,
        'request_protocol': environ.server_protocol if (
            'server_protocol' in environ else '-'),
        'request_method': environ.request_method if (
            'request_method' in environ else '-'),
        'server_port': environ.server_port if (
            'server_port' in environ else '-'),
        'query_string': environ.query_string if (
            'query_string' in environ else '-'),
        'request_uri': environ.request_uri if (
            'request_uri' in environ else '-'),
        'server_name': environ.server_name if (
            'server_name' in environ else '-'),
        'user_agent': user_agent,
        'referer': referer
    }


def log_access(connection, response_length, all_headers):
    environ = DotDict({})

    for k, v in all_headers.iteritems():
        environ[k.lower()] = v

    format_data = populate_format_data(connection, response_length, environ)
    print ("%(remote_host)s [%(timestamp)s] \"%(request_line)s\" "
        "%(status_code)s %(body_size)s \"%(referer)s\" \"%(user_agent)s\""
        % format_data)


class Connection(object):
    def __init__(self, server, accept):
        self.server = server
        self.socket, self.addr = accept

        self.read_buffer = []
        self.write_buffer = []

        self.total_received = 0
        self.request_body_received = 0
        self.request_body_length = None
        self.request_headers = None

        # Track number of failures for socket
        self.failures = 0

    def fileno(self):
        if os.name == 'posix':
            try:
                os.fstat(self.socket.fileno())
            except Exception:
                raise FDError(self)
            else:
                return self.socket.fileno()
        else:
            return self.socket.fileno()

    def handle_connect(self):
        pass

    def handle_read(self):
        try:
            data = self.socket.recv(self.server.chunk_size)
        except socket.error:
            self.fail()
            return

        if not data:
            self.close()
            return

        self.total_received += len(data)
        self.read_buffer.append(data)
        last_two_chunks = ''.join(self.read_buffer[-2:])

        if '\r\n\r\n' in last_two_chunks and not self.request_headers:
            raw_request = ''.join(self.read_buffer).split('\r\n\r\n', 1)
            self.request_body_received += len(raw_request[1])
            self.request_headers = RequestHeaders(raw_request[0])

            try:
                self.request_body_length = int(
                    self.request_headers['HTTP_CONTENT_LENGTH'])
            except (KeyError, ValueError):
                self.request_body_length = 0
            finally:
                if self.request_body_received >= self.request_body_length:
                    if self in self.server.r_list:
                        self.server.r_list.remove(self)
                    request = ''.join(self.read_buffer)

                    self.handle_request(request)

        elif self.request_headers:
            self.request_body_received += len(data)
            if self.request_body_received >= self.request_body_length:
                if self in self.server.r_list:
                    self.server.r_list.remove(self)
                request = ''.join(self.read_buffer)

                self.handle_request(request)

    def handle_write(self):
        data = self.write_buffer.pop(0)

        if data is None:
            self.close()
            return

        try:
            self.socket.send(data)
        except socket.error:
            self.fail()

        #if not self.write_buffer:
        #  self.close()

    def handle_request(self, request):
        if not request:
            self.close()
            return

        request_body = parse_body(request)

        wsgi_environ = {
            'wsgi.multiprocess': False,
            'wsgi.url_scheme': 'http',
            'wsgi.input': StringIO(request_body),
            'wsgi.multithread': True,
            'wsgi.version': (1, 0),
            'wsgi.run_once': False,
            'wsgi.errors': ''
        }

        try:
            uri_headers = RequestLine(request)
        except ValueError:
            self.close()
            return

        other_headers = {
            'SERVER_ADDR': self.server.host,
            'SERVER_PORT': self.server.port,
            'SERVER_NAME': self.server.host,
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'SERVER_SOFTWARE': 'Gimme 0.1.0',
            'REMOTE_ADDR': self.addr[0],
            'REMOTE_PORT': self.addr[1],
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SCRIPT_FILENAME': os.path.abspath(sys.argv[0]),
            'DOCUMENT_ROOT': os.getcwd() + '/',
            'PATH_TRANSLATED': os.getcwd() + '/' + uri_headers['PATH_INFO'],
            'SCRIPT_NAME': '',
            'REDIRECT_STATUS': 200
        }

        all_headers = dict(self.request_headers.items() + wsgi_environ.items()
            + other_headers.items() + uri_headers.items())

        try:
            response = self.server.app(all_headers, self.start_response)
        except Exception, e:
            response = []
            self.status = '500 Internal Server Error'
            self.headers = [('Content-Type', 'text/html')]

            response.append('<h1>500 Internal Server Error</h1>')

        finally:
            # Send headers
            headers_sent = False
            response_length = 0

            # Send response
            for i in response:
                if not headers_sent:
                    self.send_headers(self.status, self.headers)
                    headers_sent = True
                response_length += len(i)
                log_access(self, response_length, all_headers)
                self.send(i)

            self.write_buffer.append(None)

            if self not in self.server.w_list:
                self.server.w_list.append(self)

    def send_headers(self, status, headers):
        self.send("HTTP/1.1 %s\r\n" % status)
        for k, v in headers:
            self.send("%s: %s\r\n" % (k, v))
        self.send("\r\n")

    def start_response(self, status, headers, other=None):
        self.status = status
        self.headers = headers
        self.other = other

    def send(self, data):
        while data:
            chunk = data[0:self.server.chunk_size]
            self.write_buffer.append(chunk)
            data = data[self.server.chunk_size:]

        # Make sure connection is part of the write list
        #if self not in self.server.w_list:
        #  self.server.w_list.append(self)

    def shutdown(self):
        self.socket.shutdown(socket.SHUT_RDWR)

    def close(self):
        # Deprecated in favor of using e_list
        self.socket.close()

        if self in self.server.r_list:
            self.server.r_list.remove(self)
        if self in self.server.w_list:
            self.server.w_list.remove(self)
        if self in self.server.e_list:
            self.server.e_list.remove(self)

    def fail(self):
        self.failures += 1
        if self.failures == 5:
            self.close()

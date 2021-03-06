import StringIO
from gimme.uri import URI


def make_environ(method='GET', uri='/', body=''):
    uri = URI(uri)

    query_string = uri.get_query_string()
    path = uri.path

    return {
        'DOCUMENT_ROOT': '/home/user/app/dir',
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'HTTP_ACCEPT_ENCODING': 'gzip,deflate,sdch',
        'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.8',
        'HTTP_CACHE_CONTROL': 'max-age=0',
        'HTTP_CONNECTION': 'keep-alive',
        'HTTP_COOKIE': 'gimme_session=f6225d448db99e2102cc25ef9c1d123d71f132ba3705fc168bd72a717cb9638b',
        'HTTP_DNT': '1',
        'HTTP_HOST': '%s:8080' % (uri.hostname or 'localhost'),
        'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
        'HTTP_CONTENT_LENGTH': len(body),
        'PATH_INFO': uri.path,
        'PATH_TRANSLATED': '/path/to//',
        'QUERY_STRING': uri.get_query_string() or '',
        'REDIRECT_STATUS': 200,
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_PORT': 54812,
        'REQUEST_METHOD': method,
        'REQUEST_URI': path if not query_string else '%s?%s' % (path, query_string),
        'SCRIPT_FILENAME': '/path/to/file.py',
        'SCRIPT_NAME': '',
        'SERVER_ADDR': '127.0.0.1',
        'SERVER_NAME': '127.0.0.1',
        'SERVER_PORT': 8080,
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'SERVER_SOFTWARE': 'Gimme 0.1.0',
        'wsgi.errors': '',
        'wsgi.input': StringIO.StringIO(body),
        'wsgi.multiprocess': False,
        'wsgi.multithread': True,
        'wsgi.run_once': False,
        'wsgi.url_scheme': 'http',
        'wsgi.version': (1, 0)
    }

#!/usr/bin/env python

from app import app
from flup.server.fcgi import WSGIServer


if __name__ == '__main__':
    WSGIServer(app).run()

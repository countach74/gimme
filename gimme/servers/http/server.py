from .connection import Connection
import select
import socket


class HTTPServer(object):
  def __init__(self, app, host, port):
    self.app = app
    self.host = host
    self.port = port

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    self.read_list = []
    self.write_list = []
    self.except_list = []


  def start(self):
    while True:
      read_ready, write_ready, except_ready = select.select(
        self.read_list, self.write_list, self.except_list)

      for i in read_ready:
        if i is self.socket:
          conn = Connection(self, i.accept)
          self.read_list.append(conn)
          conn.handle_connect()
        else:
          i.handle_read()

      for i in write_ready:
        i.handle_write()

      for i in except_ready:
        i.handle_except()

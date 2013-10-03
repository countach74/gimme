class Connection(object):
  def __init__(self, server, accept):
    self.server = server
    self.socket, self.addr = accept()

    self.read_buffer = []
    self.write_buffer = []

    self.failures = 0

  def fileno(self):
    if os.name == 'posix':
      try:
        os.fstat(self.socket.fileno())
      except Exception:
        raise InvalidFD(self)
      else:
        return self.socket.fileno()
    else:
      return self.socket.fileno()

  def handle_connect(self):
    pass

  def handle_read(self):
    pass

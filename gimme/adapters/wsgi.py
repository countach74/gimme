class WSGIAdapter(class):
  def __init__(self, app):
    self.app = app

  def process(self, environ, start_response):
    pass

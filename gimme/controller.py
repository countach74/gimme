class Controller(object):
  def __init__(self, app, request, response):
    self.app = app
    self.request = request
    self.response = response

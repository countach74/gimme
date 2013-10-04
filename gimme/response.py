class Response(object):
  def __init__(self, route):
    self.route = route
    self.controller = route.method.im_class

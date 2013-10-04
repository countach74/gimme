class Controller(object):
  def __init__(self, app, request, response):
    self.app = app
    self.request = request
    self.response = response
    
    
class ErrorController(Controller):
  def http404(self):
    self.response.status = '404 Not Found'
    return '<h1>Oops :( - File Not Found</h1>'
  
  def http500(self):
    self.response.status = '500 Internal Server Error'
    return '<h1>Internal Server Error</h1>'
import sys
import traceback
from . import renderers


class Controller(object):
  def __init__(self, app, request, response):
    self.app = app
    self.request = request
    self.response = response
    
    
class ErrorController(Controller):
  @renderers.view('errors/404.html')
  def http404(self):
    self.response.status(404)
    return {
      'headers': self.request.headers,
    }
  
  @renderers.view('errors/500.html')
  def http500(self):
    self.response.status(500)
    e_type, e_value, e_traceback = sys.exc_info()
    traceback.print_exception(e_type, e_value, e_traceback)
    return {
      'headers': self.request.headers,
      'traceback': traceback.format_exception(e_type, e_value, e_traceback)
    }

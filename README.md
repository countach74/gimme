Gimme
=====

An ExpressJS-like web framework for Python.

Gimme's API is essentially a Pythonified version of Express (although
not asynchronous in nature). For example, a very simple application
might look something like this:


```python
import gimme
  
class RootController(gimme.Controller):
  def index(self):
    # request, response and app objects are made available to the
    # controllers via self.request, self.response, and self.app
    if 'visits' in self.requests.session:
      self.request.session['visits'] += 1
    else:
      self.requests.session['visits'] = 1
      
    return {'some data': 'hello, world!'}
    
    
# Middleware is implemented exactly as it is in Express, although
# because of the differences between Python and JavaScript,
# if you need to pass parameters to middleware upon initialization,
# you should probably create a class (with __call__() method)
# instead of a standard function.
def custom_middleware(request, response, next_):
  request.some_property = {'databases': 'are useful'}
  next_()
  
# Or, as a class:
class CustomMiddleware(object):
  def __init__(self, param1):
    self.param1 = param1
    
  def __call__(self, request, response, next_):
    request.some_property = {'something': self.param1}
    next_()
      

app = gimme.App()

app.use(gimme.middleware.compress())
app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.method_override())
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session())
app.use(gimme.middleware.body_parser())

# Assign a route to a controller and a controller to a view
app.get('/', RootController.index + 'index.html')

# Other routes can be made that allow multiple content-type handling. E.g.:
app.get('/alternate', RootController.index + (
    (gimme.Template('index.html') == 'text/html')
    (RootController.index.json() == 'application/json')
))

# ... which conditionally returns the rendered view 'index.html' or a JSON
# representation, depending on the request's "Accept" header.
#
# Or, alternatively, a separate JSON endpoint can be created like such:
app.get('/json', RootController.index.json())

# Apply CustomMiddleware to a specific route
app.get('/route_middleware', custom_middleware, RootController.index)

app.set('default headers', {
  'Content-Type': 'text/html'
})


if __name__ == '__main__':
  app.listen()
```

By default, Jinja2 is used for a template engine, but other adapters
can be written as well. More documentation to come on how to do this
(until then, check out the gimme/engines.py file). Engines are passed
to the App object on instantiation: `app = App(engine=your_engine)`.

One thing to note is that Gimme's HTTP server is, unlike Node's, a
development server and is not intended to be used for production.
Instead, Gimme apps are WSGI-compliant; you are recommended to pick
any one of the many ways of deploying a WSGI app (personally, I
recommend FastCGI via Lighttpd).

Using flup, one can turn the above example into a FastCGI app like so:

```python
from flup.server.fcgi import WSGIServer

if __name__ == '__main__':
  WSGIServer(app).run()
```

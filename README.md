Gimme
=====

A Python web framework that is very loosely based on Express JS.

Gimme is a simplistic Python web framework that looks a little bit like
Express JS, in that it has middleware and that some of the middleware and
other API calls are named similarly. It is intended to be deployed via some
sort of gevent-driven WSGI server and contains hooks to make doing so even
easier than normal.


Getting started is easy. Either clone from github and install or install via
pip:

```
pip install gimme
```


Using it's pretty easy, too.


```python
import gimme
  
class RootController(gimme.Controller):
  def index(self, request, response):
    if 'visits' in requests.session:
      request.session['visits'] += 1
    else:
      requests.session['visits'] = 1
      
    return {'some data': 'hello, world!'}
    
    
# While middleware serves the same general purpose as it does in
# Express, it is implemented quite differently in Gimme.
class CustomMiddleware(gimme.middleware.Middleware):
  def enter(self):
    # Do important things here *before* the controller method
    # is called. Oh, by the way, middleware has access to the
    # Gimme application, the current request, and current response
    # via self.app, self.request, and self.response, respectively.
    pass
    
  def exit(self):
    # Do important things here *after* the controller method has
    # been called.
    pass


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
    (gimme.Template('index.html') == 'text/html') |
    (RootController.index.json() == 'application/json')
))

# ... which conditionally returns the rendered view 'index.html' or a JSON
# representation, depending on the request's "Accept" header.
#
# Or, alternatively, a separate JSON endpoint can be created like such:
app.get('/json', RootController.index.json())

# Apply CustomMiddleware to a specific route
app.get('/route_middleware', CustomMiddleware, RootController.index)


if __name__ == '__main__':
  app.listen()
```

The above is quite a lot to type each time you want to start a new project,
so there's also a "gimme" tool for generating boilerplate stuff:

```
gimme -s your_app
```

(Creates a new project with session support.)

By default, Jinja2 is used for a template engine, but other adapters
can be written as well. More documentation to come on how to do this
(until then, check out the gimme/engines.py file). Engines are passed
to the App object on instantiation: `app = App(engine=your_engine)`.

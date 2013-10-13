Gimme
=====

An ExpressJS-like web framework for Python.

Gimme's API is essentially a Pythonified version of Express's (although
not asynchronous in nature). For example, a very simple application
might look something like this:


```python
import gimme
  
class RootController(gimme.Controller):
  @gimme.view('index.html')   # load the 'index.html' view
  def index(self):
    # request, response and app objects are made available to the
    # controllers via self.request, self.response, and self.app
    if 'visits' in self.requests.session:
      self.request.session['visits'] += 1
    else:
      self.requests.session['visits'] = 1
      
    return {'some data': 'hello, world!'}
    
    
# Middleware is implemented via Python context managers; simply
# subclass the Middleware class and implement enter() and exit()
# methods.
class CustomMiddleware(gimme.middleware.Middleware):
  def enter(self):
    # Like controllers, middleware has access to request, response
    # and app objects via self.request, self.response and self.app.
    pass
    
  def exit(self):
    pass
      

app = gimme.App()

app.use(gimme.middleware.compress())
app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.method_override())
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session())
app.use(gimme.middleware.body_parser())

app.get('/', RootController.index)

# Apply CustomMiddleware to a specific route
app.get('/route_middleware', CustomMiddleware, RootController.index)

app.set('default headers', {
  'Content-Type': 'text/html'
})


if __name__ == '__main__':
  app.listen()
```

By default, Jinja2 is used for a template engine, but other adapters
can be written as well. More documentation to come on how to do this
(until then, check out the gimme/ext/engines.py file).

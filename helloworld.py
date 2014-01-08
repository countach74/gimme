import gimme
import pickle


app = gimme.App()


class RootController(gimme.Controller):
  def index(self):
    return "Hello, world!"

  def set(self):
    self.request.session['crap'] = 'oh no!'
    return 'ok cool, set stuff'

  def get(self):
    return 'data: %s' % self.request.session.get('crap', None)

  def make_error(self):
    return crap

  def not_found(self):
    self.response.status(404)
    return "That can't be good!"

  @gimme.view('index.html')
  def test(self):
    return {}


app.routes.get('/test', RootController.test)

app.routes.get('/', RootController.index)
app.routes.get('/get', RootController.get)
app.routes.get('/set', RootController.set)
app.routes.get('/error', RootController.make_error)

app.use(gimme.middleware.compress())
app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.method_override())
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session('gimme.cache.file'))
app.use(gimme.middleware.body_parser())


if __name__ == '__main__':
  app.listen()

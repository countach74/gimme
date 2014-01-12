import gimme
import pickle
import redis


app = gimme.App()


class RootController(gimme.Controller):
  @gimme.view('index.html')
  def index(self):
    return {}

  def set(self):
    self.request.session['crap'] = 'oh no!'
    return 'ok cool, set stuff'

  def get(self):
    return 'data: %s' % self.request.session.get('crap', None)

  def make_error(self):
    raise gimme.HTTPError(403)

  def not_found(self):
    self.response.status(404)
    return "That can't be good!"

  def handle_api(self):
    print self.request.params
    return 'oh cool, everything goes here'

  def handle_upload(self):
    print self.request.body.somefile.file.read()
    return 'oh, ok'


app.routes.all('/', RootController.index)
app.routes.get('/get', RootController.get)
app.routes.get('/set', RootController.set)
app.routes.get('/error', RootController.make_error)
app.routes.get('/api/(?P<gibberish>.*?)/:user', RootController.handle_api)
app.routes.post('/submit', RootController.handle_upload)

app.use(gimme.middleware.compress())
app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.method_override())
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session('gimme.cache.redis', arguments={'redis': redis.Redis(host='10.24.1.52')}))
app.use(gimme.middleware.body_parser())


if __name__ == '__main__':
  app.listen()

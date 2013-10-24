import gimme
import pickle


app = gimme.App()


class RootController(gimme.Controller):
  def index(self):
    with open('/tmp/environ.pickle', 'w') as f:
        pickle.dump(self.request.environ, f)
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


class FormController(gimme.Controller):
  records = []
  current_id = 1

  @gimme.view('form/index.html')
  def index(self):
    return {'records': self.records}

  @gimme.view('form/show.html')
  def show(self):
    for record in self.records:
      if record['id'] == int(self.request.params.id):
        return {'record': record}
    self.response.status(404)
    return {'record': None}
    
  @gimme.view('form/new.html')
  def new(self):
    return {}

  @gimme.view('form/create.html')
  def create(self):
    id_ = self.current_id
    self.current_id += 1
    record = {
      'id': id_,
      'name': self.request.body.name,
      'data': self.request.body.data
    }
    self.records.append(record)
    return {'record': record}


app.routes.get('/', RootController.index)
app.routes.get('/get', RootController.get)
app.routes.get('/set', RootController.set)
app.routes.get('/error', RootController.make_error)

app.routes.get('/form', FormController.index)
app.routes.get('/form/new', FormController.new)
app.routes.get('/form/:id', FormController.show)
app.routes.post('/form', FormController.create)

app.routes.get('*', RootController.not_found)

app.set('default headers', {
  'Content-Type': 'text/html'
})


app.use(gimme.middleware.compress())
app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.method_override())
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session())
app.use(gimme.middleware.body_parser())


if __name__ == '__main__':
  app.listen()

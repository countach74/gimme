import gimme


app = gimme.App()


class RootController(gimme.Controller):
  @gimme.view('index.html')
  def index(self):
    return {'this': 'that'}

  def set(self):
    self.request.session['crap'] = 'oh no!'
    return 'ok cool, set stuff'

  def get(self):
    return 'data: %s' % self.request.session.get('crap', None)


app.routes.get('/', RootController.index)
app.routes.get('/get', RootController.get)
app.routes.get('/set', RootController.set)

app.set('default headers', {
  'Content-Type': 'text/html'
})


app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.method_override())
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session())
app.use(gimme.middleware.body_parser())


if __name__ == '__main__':
  app.listen()

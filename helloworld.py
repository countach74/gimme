import gimme


app = gimme.App()


class RootController(gimme.Controller):
  @gimme.view('index.html')
  def index(self):
    return {'this': 'that'}

  @gimme.format('text/html')
  def test(self):
    return {'this': 'that crap'}

  @test.add_type('application/json')
  def test(self):
    return {'some': 'test'}

  def wut(self):
    return 'this should break: %s' % wuuuut


app.routes.get('/', RootController.index)
app.routes.get('/test', RootController.test)
app.routes.get('/wut', RootController.wut)
app.set('default headers', {
  'Content-Type': 'text/html'
})


app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session())


if __name__ == '__main__':
  app.listen()

import gimme


app = gimme.App()


class RootController(gimme.Controller):
  @gimme.json()
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


app.use(gimme.Static('public'))
app.use(gimme.CookieParser())


if __name__ == '__main__':
  app.listen()

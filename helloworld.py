import gimme


app = gimme.App()


class RootController(gimme.Controller):
  @gimme.view('index.html')
  def index(self):
    return {'this': 'that'}


app.routes.get('/', RootController.index)
app.set('default headers', {
  'Content-Type': 'text/html'
})


if __name__ == '__main__':
  app.listen()

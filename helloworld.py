import gimme


app = gimme.App()


def index():
  return 'awesome!'


app.routes.get('/', index)


if __name__ == '__main__':
  app.listen()

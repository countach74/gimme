import controllers


def setup(app):
    app.routes.get('/', controllers.Root.index + 'root/index.html')
    app.routes.get('*', controllers.Root.catch_all +
        'root/catch_all.html')

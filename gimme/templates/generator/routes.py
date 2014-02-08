import controllers


def setup(app):
    app.routes.get('/', controllers.RootController.index + 'root/index.html')
    app.routes.get('*', controllers.RootController.catch_all +
        'root/catch_all.html')

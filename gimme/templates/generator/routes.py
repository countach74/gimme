import controllers


def setup(app):
    app.routes.get('/', controllers.RootController.index)
    app.routes.get('*', controllers.RootController.catch_all)

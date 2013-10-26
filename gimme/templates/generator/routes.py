import controllers


def setup(app):
    app.routes.get('/', controllers.RootController.index)

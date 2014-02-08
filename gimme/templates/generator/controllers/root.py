import gimme


class RootController(gimme.Controller):
    def index(self):
        return {}

    def catch_all(self):
        self.response.status = 404
        return {}

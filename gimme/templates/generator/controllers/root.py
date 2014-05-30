import gimme


class Root(gimme.Controller):
    def index(self, request, response):
        return {}

    def catch_all(self, request, response):
        response.status = 404
        return {}

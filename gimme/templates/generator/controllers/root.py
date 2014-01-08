import gimme


class RootController(gimme.Controller):
    @gimme.view('root/index.html')
    def index(self):
        return {}

    @gimme.view('root/catch_all.html')
    def catch_all(self):
        self.response.status(404)
        return {}

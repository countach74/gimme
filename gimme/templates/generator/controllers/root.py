import gimme


class RootController(gimme.Controller):
    @gimme.view('root/index.html')
    def index(self):
        return {}

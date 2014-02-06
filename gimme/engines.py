import sys
import os
from jinja2 import Environment, PackageLoader, FileSystemLoader, ChoiceLoader


class BaseEngine(object):
    pass
    '''
    def get_template(self, template):
        def render(data):
            return self.render(template, data)
        return render
    '''


class Jinja2Engine(BaseEngine):
    def __init__(self, template_path='views', environment=None):
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        if not environment:
            environment = Environment(loader=ChoiceLoader([
                FileSystemLoader(os.path.join(app_path, template_path)),
                PackageLoader('gimme', 'templates')
            ]))
        self.environment = environment

    def render(self, template, data):
        return self.environment.get_template(template).render(data)

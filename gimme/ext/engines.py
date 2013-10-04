import sys
import os
from jinja2 import Environment, PackageLoader, FileSystemLoader, ChoiceLoader


class Jinja2Extension(object):
  def __init__(self, environment=None):
    app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    default_template_dir = os.path.join(app_path, 'views')

    if not environment:
      environment = Environment(loader=ChoiceLoader([
        FileSystemLoader(default_template_dir),
        PackageLoader('gimme', 'views')]))

    self.environment = environment

  def __call__(self, template, params):
    return self.environment.get_template(template).render(params)

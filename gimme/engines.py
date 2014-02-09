import sys
import os
import abc
from jinja2 import Environment, PackageLoader, FileSystemLoader, ChoiceLoader


class BaseEngine(object):
    '''
    The base class that all engines should derive from.
    '''

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def render(self, template, data):
        '''
        Returns a rendered template.

        :param template: The template to render (usually a filename/path).
        :param data: The data to send to the template engine. Usually a dict.
        '''
        pass


class Jinja2Engine(BaseEngine):
    '''
    Provides Jinja2 integration.

    :param template_path: The path, relative the current working directory,
        that Jinja2 should look for templates.
    :param environment: A Jinja2 :class:`Environment <jinja2.Environment>`
        object. Defaults to ``None``. If provided, ``template_path`` is
        ignored.
    '''

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

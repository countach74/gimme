import argparse
import os
import stat
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, PackageLoader


def get_args():
    parser = argparse.ArgumentParser(
        description='Code generation tool for Gimme web framework')
    parser.add_argument('-s', '--session', action='store_true', default=False,
        help='Enable session storage.')
    parser.add_argument('appname', help='The name of the application '
        '(also denotes which directory to create the app in).')
    return parser.parse_args()


def make_dir(config, dirname=None):
    path = os.path.join(config.appname, dirname) if dirname else config.appname
    if not os.path.exists(path):
        os.mkdir(path)


def check_dir(config):
    if os.path.exists(config.appname):
        raise StandardError("App directory already exists!")


def render_file(env, config, file_path):
    return env.get_template(file_path).render(config=config)


def save_file(config, file_path, file_contents):
    path = os.path.join(config.appname, file_path)
    if os.path.exists(path):
        raise StandardError("File already exists: %s" % path)
    with open(path, 'w') as f:
        f.write(file_contents)
        trash, ext = os.path.splitext(file_path)
        if ext == '.fcgi':
            st = os.fstat(f.fileno())
            os.fchmod(f.fileno(), st.st_mode | stat.S_IXUSR | stat.S_IXGRP |
                stat.S_IXOTH)


def make_public_dirs(config):
    make_dir(config, 'public')
    make_dir(config, 'public/images')
    make_dir(config, 'public/scripts')
    make_dir(config, 'public/styles')


def main():
    config = get_args()
    check_dir(config)
    gimme_path = os.path.abspath(os.path.dirname(__file__))
    templates_path = os.path.join(gimme_path, 'templates/generator')
    env = Environment(loader=ChoiceLoader([
        FileSystemLoader(templates_path),
        PackageLoader('gimme', 'templates')
    ]))
    files = {}
    make_dir(config)

    for context, dirs, files in os.walk(templates_path):
        for i in dirs:
            full_path = os.path.join(context, i)
            dir_path = full_path[len(templates_path)+1:]
            make_dir(config, dir_path)
        for i in files:
            full_path = os.path.join(context, i)
            file_path = full_path[len(templates_path)+1:]
            trash, ext = os.path.splitext(file_path)
            if ext != '.pyc':
                file_contents = render_file(env, config, file_path)
                save_file(config, file_path, file_contents)

    make_public_dirs(config)


if __name__ == '__main__':
    main()

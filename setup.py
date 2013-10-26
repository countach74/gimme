from setuptools import setup, find_packages


setup(
    name='gimme',
    version='0.1.0',
    packages=[
        'gimme',
        'gimme.adapters',
        'gimme.ext',
        'gimme.servers',
        'gimme.servers.http',
        'gimme.servers.logger'
    ],
    package_data={
        'gimme': [
            'templates/errors/*.html',
            'templates/generator/*.py',
            'templates/generator/controllers/*.py',
            'templates/generator/public/*.*',
            'templates/generator/public/images/*.*',
            'templates/generator/public/scripts/*.*',
            'templates/generator/public/styles/*.*',
            'templates/generator/views/*.*',
            'templates/generator/views/root/*.*'
        ]
    },
    author='Tim Radke',
    author_email='countach74@gmail.com',
    license='MIT',
    test_suite='tests',
    install_requires=['jinja2', 'multipart']
)

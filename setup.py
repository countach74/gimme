from setuptools import setup, find_packages


setup(
    name='gimme',
    version='0.1.6',
    packages=[
        'gimme',
        'gimme.ext',
        'gimme.servers',
        'gimme.servers.logger',
        'gimme.parsers'
    ],
    package_data={
        'gimme': [
            'templates/errors/*.html',
            'templates/generator/*.py',
            'templates/generator/*.fcgi',
            'templates/generator/controllers/*.py',
            'templates/generator/public/*.*',
            'templates/generator/public/images/*.*',
            'templates/generator/public/scripts/*.*',
            'templates/generator/public/styles/*.*',
            'templates/generator/views/*.*',
            'templates/generator/views/root/*.*'
        ]
    },
    entry_points={
      'console_scripts': [
        'gimme = gimme.generator:main'
      ],
      'dogpile.cache': [
        'gimme.cache.memory = gimme.cache:Memory',
        'gimme.cache.file = gimme.cache:File',
        'gimme.cache.redis = gimme.cache:Redis'
      ]
    },
    author='Tim Radke',
    author_email='countach74@gmail.com',
    download_url='https://github.com/countach74/gimme/tarball/master',
    description='An ExpressJS-inspired web framework... in Python',
    license='MIT',
    test_suite='tests',
    install_requires=['jinja2', 'dogpile.cache', 'gevent'],
)

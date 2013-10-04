from setuptools import setup, find_packages


setup(
  name='gimme',
  version='0.1.0',
  packages = [
    'gimme',
    'gimme.adapters',
    'gimme.ext'
  ],
  author='Tim Radke',
  author_email='countach74@gmail.com',
  license='MIT',
  test_suite='tests'
)

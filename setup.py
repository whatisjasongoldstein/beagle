from distutils.core import setup
from setuptools import find_packages

setup(
    name='Beagle',
    version="0.1",
    author='Jason Goldstein',
    author_email='jason@betheshoe.com',
    url='https://github.com/whatisjasongoldstein/beagle',
    packages=find_packages(),
    include_package_data=True,
    description="For making static sites. Also a dog that's too smart for its own good",
    long_description=open('README.md').read(),
)
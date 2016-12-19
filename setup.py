#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
python-utils
======
python-utils is a set of generic Python utilities which currently target
Python 2.7.X environments with no other required dependencies.  The code
targets both general production code as well as test utilities to facilitate
easier test generation, management and complexity.
This library is not currently intended to be generally useful to the community at
large as there is work to be done to provide greater Python support as well as
general documentation and upkeep, but has been used successfully in production
environments within the prescribed environments.

"""
# future/compat
from __future__ import absolute_import
from __future__ import print_function

# stdlib
import io
import os
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


def get_version(package):
    with open(os.path.join(os.path.split(__file__)[0], 'src', package, '__version__.py'), "r") as init_file:
        for line in init_file.readlines():
            if line.startswith("__version_str__ = "):
                _, val = line.split("=")
                val = eval(val.strip())
                return val

version = get_version("generic_utils")


setup(
    name='generic_utils',
    version=version,
    license='MIT',
    description='A set of generic utility classes and helper functions for Python development.',
    long_description=read('README.rst'),
    author='Kevin Seelbach',
    author_email='kevin.seelbach@gmail.com',
    url='https://github.com/kevinseelbach/generic_utils',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    #py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    package_data={'generic_utils.pylint_tools': ['transforms/**']},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],
    extras_require={
        'html': [
            'beautifulsoup4>=4.3.2',
            'requests',
            'lxml',
        ],
        'cassandra': [
            'cassandra-driver'
        ],
        'celery_test': [
            'celery>=3.1.20',
            'redis',
            'celery_testutils',
            'celery[threads]'
        ],
        'elasticsearch': [
            'elasticsearch',
        ],
        'statsd': [
            'statsd'
        ],
        'test_utils': [
            'ddt',
            'freezegun',
            'mock'
        ]
    },
    install_requires=[
        'setuptools',
        'six',
        'future',
    ]
)

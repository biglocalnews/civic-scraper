#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def read_reqs(name):
    dir = os.path.dirname(__file__)
    reqs_path = os.path.join(dir, name)
    with open(reqs_path) as fh:
        reqs = [line.strip() for line in fh.readlines()]
        return reqs

requirements = [
    'bs4',
    'requests',
]

#requirements = read_reqs('requirements.txt')

test_requirements = [
    'flake8',
    'pytest',
    'pytest-vcr',
    'vcrpy',
]

setup(
    name='civic-scraper',
    version='0.1.0',
    description="Command-line tool and library for scraping government agendas, minutes and other public records.",
    #long_description=__doc__,
    author="Serdar Tumgoren",
    author_email='zstumgoren@gmail.com',
    url='https://github.com/biglocalnews/civic-scraper',
    #TODO: Specify civic_scraper/ instead of find_packages?
    # (because tests/ is also a package...?)
    packages=find_packages(),
    include_package_data=True,
    #TODO: Verify this is click-based
    entry_points='''
        [console_scripts]
        civic-scraper=civic_scraper.cli:cli
    ''',
    install_requires=requirements,
    license="Apache 2.0 license",
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    tests_require=test_requirements
)

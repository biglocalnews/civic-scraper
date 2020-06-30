#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

requirements = [
    'bs4',
    'requests',
    'retrying',
]

test_requirements = [
    'flake8',
    'pytest',
#    'vcrpy',
#    'pytest-vcr'
]

setup(
    name='civic-scraper',
    version='0.1.0',
    description="Command-line tool for scraping government agendas, minutes and other public records.",
    #long_description=__doc__,
    author="Amy DiPierro",
    TKKauthor_email='adipier1@gmail.com',
    url='https://github.com/biglocalnews/civic-scraper',
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        civic-scraper=civic_scraper.cli:cli
    ''',
    install_requires=requirements,
    license="ISC license",
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    tests_require=test_requirements
)

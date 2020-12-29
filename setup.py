#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
civic-scraper
-------------

`civic-scraper` helps download `agendas`_, `minutes`_ and other documents produced by government.
It includes a command-line tool and reusable Python code to scrape a growing number
of public agency websites.

* Docs: http://civic-scraper.readthedocs.io/en/latest/
* GitHub: https://github.com/biglocalnews/civic-scraper
* PyPI: https://pypi.python.org/pypi/civic-scraper
* Free and open source software: `Apache license`_

.. _Apache license: https://github.com/biglocalnews/civic-scraper/blob/master/LICENSE
.. _agendas: https://en.wikipedia.org/wiki/Agenda_(meeting)
.. _minutes: https://en.wikipedia.org/wiki/Minutes

Basic install and usage
-----------------------


Install civic-scraper_::

   pip install civic-scraper

...and start scraping from the command line::

   # Scrape today's agendas and minutes from a CivicPlus site
   civic-scraper scrape --download --url http://nc-nashcounty.civicplus.com/AgendaCenter

Or in a script::

  # Scrape today's agendas and minutes from a CivicPlus site
  from civic_scraper.platforms import CivicPlusSite
  url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
  site = CivicPlusSite(url)
  site.scrape(download=True)

See the `official docs`_ for more details on usage.

.. _official docs: http://civic-scraper.readthedocs.io/en/latest/
"""

import os
from setuptools import setup, find_packages

requirements = [
    'bs4',
    'click',
    'click-option-group',
    'requests',
]

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
    long_description=__doc__,
    author="Serdar Tumgoren",
    author_email='zstumgoren@gmail.com',
    url='https://github.com/biglocalnews/civic-scraper',
    packages=find_packages(),
    include_package_data=True,
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

#!/usr/bin/env python
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

from setuptools import find_packages, setup


def read(file_name):
    """Read the provided file."""
    this_dir = os.path.dirname(__file__)
    file_path = os.path.join(this_dir, file_name)
    with open(file_path) as f:
        return f.read()


def version_scheme(version):
    """
    Version scheme hack for setuptools_scm.
    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342
    If that issue is resolved, this method can be removed.
    """
    import time

    from setuptools_scm.version import guess_next_version

    if version.exact:
        return version.format_with("{tag}")
    else:
        _super_value = version.format_next_version(guess_next_version)
        now = int(time.time())
        return _super_value + str(now)


def local_version(version):
    """
    Local version scheme hack for setuptools_scm.
    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342
    If that issue is resolved, this method can be removed.
    """
    return ""


requirements = [
    "bs4",
    "click",
    "click-option-group",
    "feedparser",
    "requests",
    "scraper-legistar",
]

test_requirements = [
    "flake8",
    "pytest",
    "pytest-vcr",
    "vcrpy",
]

setup(
    name="civic-scraper",
    description="Tools for downloading agendas, minutes and other documents produced by local government",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Serdar Tumgoren",
    author_email="zstumgoren@gmail.com",
    url="https://github.com/biglocalnews/civic-scraper",
    packages=find_packages(),
    include_package_data=True,
    entry_points="""
        [console_scripts]
        civic-scraper=civic_scraper.cli:cli
    """,
    install_requires=requirements,
    license="Apache 2.0 license",
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    setup_requires=["setuptools_scm"],
    use_scm_version={"version_scheme": version_scheme, "local_scheme": local_version},
)


.. image:: https://img.shields.io/pypi/v/civic-scraper.svg
        :target: https://pypi.python.org/pypi/civic-scraper

.. image:: https://img.shields.io/pypi/pyversions/civic-scraper.svg
        :target: https://pypi.python.org/pypi/civic-scraper

.. image:: https://img.shields.io/travis/biglocalnews/civic-scraper.svg
        :target: https://travis-ci.com/biglocalnews/civic-scraper

.. image:: https://readthedocs.org/projects/civic-scraper/badge/?version=latest
        :target: https://civic-scraper.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

=============
Civic Scraper
=============

Overview
========

`civic-scraper` helps download `agendas`_, `minutes`_ and other documents produced by government.
It includes a command-line tool and reusable Python code to scrape a growing number
of public agency websites.

* Documentation: http://civic-scraper.readthedocs.io/en/latest/
* GitHub: https://github.com/biglocalnews/civic-scraper
* PyPI: https://pypi.python.org/pypi/civic-scraper
* Free and open source software: `Apache license`_

.. _Apache license: https://github.com/biglocalnews/civic-scraper/blob/master/LICENSE
.. _agendas: https://en.wikipedia.org/wiki/Agenda_(meeting)
.. _minutes: https://en.wikipedia.org/wiki/Minutes

Quickstart
==========

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

.. note:: There are many more options for customizing scrapes,
          especially by date range.  Check out the :ref:`usage` docs for details.

          See the :ref:`install` docs to configure the download location.



.. _civic-scraper: https://github.com/biglocalnews/civic-scraper
.. _civic-scraper docs: https://civic-scraper.readthedocs.io/en/latest/

# civic-scraper

Tools for downloading agendas, minutes and other documents produced by local government

## Links

- Documentation: <http://civic-scraper.readthedocs.io/en/latest/>
- GitHub: <https://github.com/biglocalnews/civic-scraper>
- PyPI: <https://pypi.python.org/pypi/civic-scraper>
- Free and open source software: [Apache license]

## Quickstart

Install [civic-scraper]:

```
pip install civic-scraper
```

...and start scraping from the command line:

```
# Scrape today's agendas and minutes from a CivicPlus site
civic-scraper scrape --download --url http://nc-nashcounty.civicplus.com/AgendaCenter
```

Or in a script:

```
# Scrape today's agendas and minutes from a CivicPlus site
from civic_scraper.platforms import CivicPlusSite
url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
site = CivicPlusSite(url)
site.scrape(download=True)
```

:::{note}
There are many more options for customizing scrapes,
especially by date range.  Check out the {ref}`usage` docs for details.

See the {ref}`install` docs to configure the download location.
:::

## Documentation

```{toctree}
install
usage
contributing
```

[agendas]: https://en.wikipedia.org/wiki/Agenda_(meeting)
[apache license]: https://github.com/biglocalnews/civic-scraper/blob/master/LICENSE
[civic-scraper]: https://github.com/biglocalnews/civic-scraper
[civic-scraper docs]: https://civic-scraper.readthedocs.io/en/latest/
[minutes]: https://en.wikipedia.org/wiki/Minutes

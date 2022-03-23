(install)=

# Getting started

Install the library from the Python Package Index.

```
pipenv install civic-scraper
```

Upon installation, you should have access to the {code}`civic-scraper` tool on the command line:

```bash
pipenv run civic-scraper --help
```

... and start scraping from the command line:

```bash
pipenv run civic-scraper scrape --download --url http://nc-nashcounty.civicplus.com/AgendaCenter
```

Or in a script:

```python
from civic_scraper.platforms import CivicPlusSite

url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
site = CivicPlusSite(url)
site.scrape(download=True)
```

```{note}
There are many more options for customizing scrapes, especially by date range.  Check out the {ref}`usage` docs for details. See the {ref}`install` docs to configure the download location.
```

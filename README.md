# civic-scraper

`civic-scraper` is a Python package that helps identify and download agendas, minutes and other file assets related to government meetings from local public agencies around the U.S.

License: [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)

> See our [official documentation](https://civic-scraper.readthedocs.io/en/latest/?badge=latest)
> more details on usage and ways to [contribute]().

```
pip install civic-scraper

```

Scrape today's agendas and minutes on the command-line:

```
civic-scraper --download --url https://ca-eastpaloalto.civicplus.com/AgendaCenter
```

Or in a script:

```
from civic_scraper.scrapers import CivicPlusSite
url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter'
site = CivicPlusSite(url)
assets = site.scrape(download=True)
```

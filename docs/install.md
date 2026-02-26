(install)=

# Getting started

## Install

Install the library from the Python Package Index.

We like to use[uv](https://docs.astral.sh/uv/getting-started/installation/) for Python project and package management, bit `pip`
is the most common way to install Python packages. We'll describe
the `uv` setup steps and the `pip` ones. Steps might look a little
bit different if you use another package installer, like `pipenv`.

```shell
uv add civic-scraper
```

or

```shell
pip install civic-scraper
```

## Run the command line tool

After installation, you can run {code}`civic-scraper` on the command line:

```shell
uv run civic-scraper --help
```

or

```shell
civic-scraper --help
```

Here's an example run:

```shell
uv run civic-scraper scrape --download --url http://nc-nashcounty.civicplus.com/AgendaCenter
```

```shell
civic-scraper scrape --download --url http://nc-nashcounty.civicplus.com/AgendaCenter
```

## Use civic_scraper in your Python code

The `civic_scraper` package is primarily developed as a code library,
which you can use in your own Python projects, like this:

```python
from civic_scraper.platforms import CivicPlusSite

url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
site = CivicPlusSite(url)
site.scrape(download=True)
```

```{note}
There are many more options for customizing scrapes, especially by date range.  Check out the {ref}`usage` docs for details. See the {ref}`install` docs to configure the download location.
```

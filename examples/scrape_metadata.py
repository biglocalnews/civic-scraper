"""
Example of scraping metadat by date for a single CivicPlus site.

NOTE: CivicScraper must be installed to use this script.
Below USAGE shows how to run from the root of this repo.

USAGE:

    cd civic-scraper/
    pipenv install
    pipenv shell
    PYTHONPATH=${PWD} python examples/scrape_metadata.py

"""
from civic_scraper.platforms import CivicPlusSite

print("Scraping metadata for Las Cruces, NM...")
url = 'https://nm-lascruces.civicplus.com/AgendaCenter/'
site = CivicPlusSite(url)
assets_metadata = site.scrape(start_date='2020-12-17', end_date='2020-12-17')

outdir = '/tmp'
outfile = assets_metadata.to_csv(outdir)
print(f"Exported {outfile}")

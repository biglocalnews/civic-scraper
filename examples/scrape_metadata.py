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
from civic_scraper.scrapers import CivicPlusSite

print("Scraping metadata for Columbus, WI...")
url = 'http://wi-columbus.civicplus.com/AgendaCenter'
site = CivicPlusSite(url)
assets_metadata = site.scrape(start_date='2020-10-01', end_date='2020-10-09')

outfile = '/tmp/columbus-wi.csv'
print(f'Exporting metadata to {outfile}')
assets_metadata.to_csv(outfile)

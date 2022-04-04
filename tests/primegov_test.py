import pytest
import logging
from civic_scraper.platforms import PrimeGovSite

logging.basicConfig(level="DEBUG")

primegov_sites = [
    {'site': 'https://lacity.primegov.com/api/meeting/',
     'config': {
        'place': 'los angeles',
        'state_or_province': 'ca',
     },
    },
]

def primegov_integration():

    for obj in primegov_sites:
        scraper = PrimeGovSite(obj['site'])
        data = scraper.scrape()
        assert len(data) > 0

if __name__ == '__main__':
    primegov_integration()


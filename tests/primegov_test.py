import pytest
import logging
from civic_scraper.platforms import PrimeGovSite

logging.basicConfig(level="DEBUG")

primegov_sites = [
    {'site': 'https://lacity.primegov.com/api/meeting/search?CommitteeId=&from=3%2F30%2F2022&text=&to=3%2F31%2F2022',
     'config': {
        'place': 'brookhaven',
        'state_or_province': 'ga',
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


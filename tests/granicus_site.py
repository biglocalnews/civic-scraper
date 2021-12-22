import pytest
import logging
from civic_scraper.platforms import GranicusSite

logging.basicConfig(level="DEBUG")

granicus_sites = [
    {'site': 'https://brookhavencityga.iqm2.com/Services/RSS.aspx?Feed=Calendar',
     'config': {},
    },
    {'site': 'https://eastpointcityga.iqm2.com/Services/RSS.aspx?Feed=Calendar',
     'config': {},
    },
    {'site': 'https://atlantacityga.iqm2.com/Services/RSS.aspx?Feed=Calendar',
     'config': {},
    },
]

def granicus_integration():
    for obj in granicus_sites:
        scraper = GranicusSite(obj['site'])
        data = scraper.scrape()
        breakpoint()
        assert len(data) > 0

if __name__ == '__main__':
    granicus_integration()
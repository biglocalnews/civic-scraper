import pytest
import logging
from civic_scraper.platforms import LegistarSite

logging.basicConfig(level="DEBUG")

legistar_sites = [
    {'site': 'http://kpb.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Alaska',
     }
    },
    {'site': 'http://matanuska.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Alaska',
     }
    },
    {'site': 'http://npfmc.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Alaska',
     }
    },
    {'site': 'http://petersburg.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Alaska',
     }
    },
    {'site': 'http://sitka.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Alaska',
     }
    },
    {'site': 'http://valdez.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Alaska',
     }
    },
    {'site': 'http://baldwincountyal.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Central',
     }
    },
    {'site': 'http://cityoffoley.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Central',
     }
    },
    {'site': 'http://accessfayetteville.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Central',
     }
    },
    {'site': 'http://jonesboro.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Central',
     }
    },
    {'site': 'http://apachejunction.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://goodyear.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://lakehavasucity.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://maricopa.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://mesa.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://paradisevalleyaz.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://phoenix.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://pima.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://yuma-az.legistar.com/Calendar.apx',
     'config': {
        'timezone': 'US/Arizona',
     }
    },
    {'site': 'http://alameda.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://actransit.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://burlingameca.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://carson.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://cathedralcity.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://chulavista.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://cityofcommerce.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://corona.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://culver-city.legistar.com/Calendar.apx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://cupertino.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
    {'site': 'http://eldorado.legistar.com/Calendar.aspx',
     'config': {
        'timezone': 'US/Pacific',
     }
    },
]

def test_integration():
    for obj in legistar_sites:
        scraper = LegistarSite(obj['site'], **obj['config'])
        data = scraper.scrape()
        assert len(data) > 10

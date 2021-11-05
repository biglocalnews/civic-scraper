import pytest


def test_integration():
    # get first 30 sites & timezones (from states) from legistar sites spreadsheet
    # use state info to get timezone
    # use below loop to instantiate scrapers
    for site, config in [list of (site, config)]:
        scraper = LegistarSite(site, config)
        data = scraper.scrape()
        assert len(data) > 10
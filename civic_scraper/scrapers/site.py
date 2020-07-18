"""
Base Site class.
"""
from civic_scraper.asset import AssetCollection


class Site(object):

    def scrape(self, **scrape_args) -> AssetCollection:
        """
        Scrape the site and return a AssetList instance.
        """
        raise NotImplementedError


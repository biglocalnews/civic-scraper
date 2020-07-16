"""
Base Site class.
"""
from civic_scraper.asset import AssetList

class Site(object):

    def scrape(self, **scrape_args) -> AssetList:
        """
        Scrape the site and return a AssetList instance.
        """
        raise NotImplementedError

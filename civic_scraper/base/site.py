import datetime

from .asset import AssetCollection
from .cache import Cache


class Site:
    """Base class for all Site scrapers.

    Args:
        base_url (int): URL to a government agency site
        cache (Cache instance): Optional Cache instance
            (default: ".civic-scraper" in user home dir)
        parser_kls (class): Optional parser class to extract
            data from government agency websites.

    """

    def __init__(self, base_url, cache=Cache(), parser_kls=None):
        self.runtime = datetime.datetime.utcnow().date()
        self.url = base_url
        self.cache = cache
        if parser_kls:
            self.parser_kls = parser_kls

    def scrape(self, *args, **kwargs) -> AssetCollection:
        """
        Scrape the site and return an AssetCollection instance.
        """
        raise NotImplementedError

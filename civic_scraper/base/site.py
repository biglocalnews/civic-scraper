import datetime

from .asset import AssetCollection
from .cache import Cache


class Site:
    """Base class for all Site scrapers.

    Args:
        base_url (int): URL to a government agency site
        cache (Cache instance): Optional Cache instance
            (default: ".civic-scraper" in user home dir)

    """

    def __init__(self, base_url, cache=Cache()):
        self.runtime = datetime.datetime.utcnow().date()
        self.url = base_url
        self.cache = cache

    def scrape(self, *args, **kwargs) -> AssetCollection:
        """
        Scrape the site and return an AssetCollection instance.
        """
        raise NotImplementedError

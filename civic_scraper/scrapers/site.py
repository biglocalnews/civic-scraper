"""
Base Site class.
"""
from civic_scraper.document import DocumentList


class Site(object):

    def scrape(self, **scrape_args) -> DocumentList:
        """
        Scrape the site and return a DocumentList instance.
        """
        raise NotImplementedError

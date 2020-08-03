"""
Base Site class.
"""
from civic_scraper.asset import AssetCollection

class Site(object):

    def scrape(
            self,
            start_date=None,
            end_date=None,
            download=False,
            target_dir=None,
            file_size=None,
            asset_list=SUPPORTED_ASSET_TYPES,
            csv_export=None,
            append=False
    ): -> AssetCollection:
        """
        Scrape the site and return a AssetList instance.
        """
        raise NotImplementedError


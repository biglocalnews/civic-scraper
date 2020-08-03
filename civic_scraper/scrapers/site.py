"""
Base Site class.
"""
from civic_scraper.asset import AssetCollection
SUPPORTED_ASSET_TYPES = ['agenda', 'minutes', 'audio', 'video', 'video2', 'agenda_packet', 'captions']

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
    ) -> AssetCollection:
        """
        Scrape the site and return a AssetList instance.
        """
        raise NotImplementedError


from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache

class GranicusSite(base.Site):
    def __init__(self,
                 base_url,
                 event_info_keys = {'meeting_details_info': 'Meeting Details',
                                    'meeting_date_info': 'Meeting Date',
                                    'meeting_time_info': 'Meeting Time',
                                    'meeting_location_info': 'Meeting Location'},
                 cache=Cache(),
                 parser_kls=None, timezone=None):
        super().__init__(base_url, cache, parser_kls)
        self.granicus_instance = urlparse(base_url).netloc.split('.')[0]
        self.timezone = timezone
        self.event_info_keys = event_info_keys

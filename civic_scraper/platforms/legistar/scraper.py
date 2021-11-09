import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache

from legistar.events import LegistarEventsScraper

from datetime import datetime, time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Scrape today's agendas and minutes from a Legistar site
class LegistarSite(base.Site):

    def __init__(self, base_url, cache=Cache(), parser_kls=None, timezone=None):
        super().__init__(base_url, cache, parser_kls)
        self.legistar_instance = urlparse(base_url).netloc.split('.')[0]
        self.timezone = timezone

    def create_asset(self, event, scraper):
        # get date and time of event
        if not event['Meeting Time']:
            meeting_datetime = " ".join((event['Meeting Date'], time(0, 0, 0)))
        else:
            meeting_datetime = " ".join((event['Meeting Date'], event['Meeting Time']))
        meeting_date = scraper.toDate(meeting_datetime)
        meeting_time = scraper.toTime(meeting_datetime)

        # get event ID
        if type(event['Meeting Details']) == dict:
            url = event['Meeting Details']['url']
            query_dict = parse_qs(urlparse(url).query)

            meeting_id = 'legistar_{}_{}'.format(self.legistar_instance, query_dict['ID'][0])
        else:
            # No meeting details, e.g., event is in future
            url = None
            meeting_id = None

        # get event name
        if type(event['Name']) == dict:
            asset_name = event['Name']['label']
            committee_name = event['Name']['label']
        else:
            asset_name = event['Name']
            committee_name = event['Name']

        e = {'url': url,
             'asset_name': asset_name,
             'committee_name': committee_name,
             'place': event['Meeting Location'],
             'state_or_province': None,
             'asset_type': 'Agenda',
             'meeting_date': meeting_date.strip(),
             'meeting_time': meeting_time,
             'meeting_id': meeting_id,
             'scraped_by': f'civic-scraper_{civic_scraper.__version__}',
             'content_type': 'txt',
             'content_length': None,
        }
        return Asset(**e)

    def scrape(self, download=True):
        webscraper = LegistarEventsScraper(retry_attempts=3)

        # required to instantiate webscraper
        webscraper.BASE_URL = urlparse(self.url).netloc
        webscraper.EVENTSPAGE = self.url
        webscraper.TIMEZONE = self.timezone
        webscraper.date_format = '%m/%d/%Y %I:%M %p'

        ac = AssetCollection()
        assets = [self.create_asset(event[0], webscraper) for event in webscraper.events(since=2021)]
        for a in assets:
            ac.append(a)

        if download:
            asset_dir = Path(self.cache.path, 'assets')
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    dir_str = str(asset_dir)
                    asset.download(target_dir=dir_str, session=webscraper)
        return ac

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection

from legistar.events import LegistarEventsScraper

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Scrape today's agendas and minutes from a Legistar site
class LegistarSite(base.Site):
    # do not overwrite init method
    # base.Site's init has what we need for now
    def create_asset(self, event, scraper):
        # get date and time of event
        meeting_datetime_tuple = (event[0]['Meeting Date'], event[0]['Meeting Time'])
        meeting_datetime = " ".join(meeting_datetime_tuple)
        meeting_date = scraper.toDate(meeting_datetime)
        meeting_time = scraper.toTime(meeting_datetime)

        # get event ID
        url = event[0]['Meeting Details']['url']
        _, _, _, _, query, _ = urlparse(url)

        query_dict = parse_qs(query)

        meeting_id = 'legistar_ga-canton_{}'.format(query_dict['ID'][0])

        e = {'url': url,
             'asset_name': event[0]['Name']['label'],
             'committee_name': event[0]['Name']['label'],
             'place': event[0]['Meeting Location'],
             'state_or_province': None,
             'asset_type': 'Agenda',
             'meeting_date': meeting_date, 
             'meeting_time': meeting_time,
             'meeting_id': meeting_id,
             'scraped_by': f'civic-scraper_{civic_scraper.__version__}',
             'content_type': 'txt',
             'content_length': None,
        }
        return Asset(**e)

    def scrape(self, download=True):
        webscraper = LegistarEventsScraper(
            # requests_per_minute=self.requests_per_minute,
            retry_attempts=3)

        # if self.cache_storage:
        #     webscraper.cache_storage = self.cache_storage

        # webscraper.cache_write_only = self.cache_write_only

        webscraper.BASE_URL = "https://canton.legistar.com/"
        webscraper.EVENTSPAGE = "https://canton.legistar.com/Calendar.aspx"
        webscraper.TIMEZONE = 'UTC'
        webscraper.date_format = '%m/%d/%Y %I:%M %p'

        ac = AssetCollection()
        assets = [self.create_asset(event, webscraper) for event in webscraper.events(since=2021)]
        for a in assets:
            ac.append(a)

        if download:
            asset_dir = Path(self.cache.path, 'assets')
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                # if self._skippable(asset, file_size, asset_list):
                    # continue
                dir_str = str(asset_dir)
                asset.download(dir_str, session=webscraper)
        return ac

if __name__ == "__main__":
    url = "https://canton.legistar.com/Calendar.aspx"
    site = LegistarSite(url)
    assets = site.scrape(download=True)
    assets.to_csv(site.cache.metadata_files_path)

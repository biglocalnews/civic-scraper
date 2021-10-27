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
        meeting_datetime = " ".join((event['Meeting Date'], event['Meeting Time']))
        meeting_date = scraper.toDate(meeting_datetime)
        meeting_time = scraper.toTime(meeting_datetime)

        # get event ID
        if type(event['Meeting Details']) == dict:
            url = event['Meeting Details']['url']
            query_dict = parse_qs(urlparse(url).query)

            meeting_id = 'legistar_ga-wellington_{}'.format(query_dict['ID'][0])
        else:
            # No meeting details, e.g., event is in future
            url = None
            meeting_id = None


        e = {'url': url,
             'asset_name': event['Name'],
             'committee_name': event['Name'],
             'place': event['Meeting Location'],
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
        webscraper = LegistarEventsScraper(retry_attempts=3)

        webscraper.BASE_URL = "https://wellington.legistar.com/"
        webscraper.EVENTSPAGE = self.url
        webscraper.TIMEZONE = 'EST'
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

if __name__ == "__main__":
    url = "https://wellington.legistar.com/Calendar.aspx"
    site = LegistarSite(url)
    assets = site.scrape(download=True)
    assets.to_csv(site.cache.metadata_files_path)

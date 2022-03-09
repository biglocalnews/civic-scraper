import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from legistar.events import LegistarEventsScraper

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache


# Scrape today's agendas and minutes from a Legistar site
class LegistarSite(base.Site):
    def __init__(
        self,
        base_url,
        event_info_keys={
            "meeting_details_info": "Meeting Details",
            "meeting_date_info": "Meeting Date",
            "meeting_time_info": "Meeting Time",
            "meeting_location_info": "Meeting Location",
        },
        cache=Cache(),
        parser_kls=None,
        timezone=None,
    ):
        super().__init__(base_url, cache, parser_kls)
        self.legistar_instance = urlparse(base_url).netloc.split(".")[0]
        self.timezone = timezone
        self.event_info_keys = event_info_keys

    def create_asset(self, event, scraper):
        detail_info = event[self.event_info_keys["meeting_details_info"]]
        date_info = event[self.event_info_keys["meeting_date_info"]]
        time_info = event[self.event_info_keys["meeting_time_info"]] or None
        location_info = None
        if self.event_info_keys["meeting_location_info"] in event.keys():
            location_info = event[self.event_info_keys["meeting_location_info"]]

        time_format = None
        if time_info:
            time_format = re.match(r"\d*?:\d{2} \w{2}", time_info)

        if time_format:
            meeting_datetime = " ".join((date_info, time_info))
        else:
            meeting_datetime = " ".join((date_info, "12:00 AM"))

        meeting_date = scraper.toDate(meeting_datetime)
        meeting_time = scraper.toTime(meeting_datetime)

        # use regex to match pattern #/#/#; raise warning if no match

        # get event ID
        if type(event[scraper.event_info_key]) == dict:
            url = detail_info["url"]
            query_dict = parse_qs(urlparse(url).query)

            meeting_id = "legistar_{}_{}".format(
                self.legistar_instance, query_dict["ID"][0]
            )
        else:
            # No meeting details, e.g., event is in future
            url = None
            meeting_id = None

        # get event name
        if type(event["Name"]) == dict:
            asset_name = event["Name"]["label"]
            committee_name = event["Name"]["label"]
        else:
            asset_name = event["Name"]
            committee_name = event["Name"]

        e = {
            "url": url,
            "asset_name": asset_name,
            "committee_name": committee_name,
            "place": location_info,
            "state_or_province": None,
            "asset_type": "Agenda",
            "meeting_date": meeting_date.strip(),
            "meeting_time": meeting_time,
            "meeting_id": meeting_id,
            "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
            "content_type": "txt",
            "content_length": None,
        }
        return Asset(**e)

    def scrape(self, download=True):
        webscraper = LegistarEventsScraper(
            event_info_key=self.event_info_keys["meeting_details_info"],
            retry_attempts=3,
        )

        # required to instantiate webscraper
        webscraper.BASE_URL = urlparse(self.url).netloc
        webscraper.EVENTSPAGE = self.url
        webscraper.TIMEZONE = self.timezone
        webscraper.date_format = "%m/%d/%Y %I:%M %p"

        ac = AssetCollection()
        assets = [
            self.create_asset(event[0], webscraper)
            for event in webscraper.events(since=2021)
        ]
        for a in assets:
            ac.append(a)

        if download:
            asset_dir = Path(self.cache.path, "assets")
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    dir_str = str(asset_dir)
                    asset.download(target_dir=dir_str, session=webscraper)
        return ac

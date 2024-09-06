import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from legistar.events import LegistarEventsScraper

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.utils import parse_date, dtz_to_dt, mb_to_bytes, today_local_str


class Site(base.Site):
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

    def scrape(
        self,
        start_date=None,
        end_date=None,
        download=False,
        file_size=None,
        asset_list=["Agenda", "Minutes"],
    ):
        """Scrape a government website for metadata and/or docs.
        Args:
            start_date (str): YYYY-MM-DD (default: current day)
            end_date (str): YYYY-MM-DD (default: current day)
            download (bool): Download file assets such as PDFs (default: False)
            file_size (float): Max size in Megabytes of file assets to download
            asset_list (list): Optional list of SUPPORTED_ASSET_TYPES to
                to limit items to be scraped (e.g. agenda, minutes). (default: [])
        Returns:
            AssetCollection: A sequence of Asset instances
        """
        # Use current day as default
        today = today_local_str()
        start_date = start_date or today
        end_date = end_date or today
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
        start_year = int(start_date[:4])
        events = [event[0] for event in webscraper.events(since=start_year)]
        for event in events:
            meeting_meta = self._extract_meeting_meta(event, webscraper)
            for asset_type in asset_list:
                # Skip if a dictionary containing 'url' key is not present for the given asset type
                try:
                    asset = self._create_asset(event, meeting_meta, asset_type)
                except TypeError:
                    continue
                # Apply date and other filters
                if self._skippable(
                    asset, start_date, end_date, file_size=file_size, download=download
                ):
                    continue
                ac.append(asset)
        if download:
            asset_dir = Path(self.cache.path, "assets")
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    dir_str = str(asset_dir)
                    asset.download(target_dir=dir_str, session=webscraper)
        return ac

    def _add_file_meta(self, asset):
        headers = requests.head(asset.url, allow_redirects=True).headers
        asset.content_type = headers["content-type"]
        asset.content_length = headers["content-length"]

    def _create_asset(self, event, meeting_meta, asset_type):
        name_bits = [self._event_name(event)]
        meeting_id = meeting_meta["meeting_id"]
        if meeting_id:
            clean_id = meeting_id.split("_")[-1]
            name_bits.append(clean_id)
        name_bits.append(asset_type)
        kwargs = {
            "url": event[asset_type]["url"],
            "asset_type": asset_type.lower().replace(" ", "_"),
            "asset_name": " - ".join(name_bits),
            "content_type": None,
            "content_length": None,
        }
        kwargs.update(meeting_meta)
        return Asset(**kwargs)

    def _extract_meeting_meta(self, event, scraper):
        detail_info = event[self.event_info_keys["meeting_details_info"]]
        date_info = event[self.event_info_keys["meeting_date_info"]]
        time_info = event[self.event_info_keys["meeting_time_info"]] or None
        time_format = None
        if time_info:
            time_format = re.match(r"\d*?:\d{2} \w{2}", time_info)

        if time_format:
            meeting_datetime = " ".join((date_info, time_info))
        else:
            meeting_datetime = " ".join((date_info, "12:00 AM"))

        meeting_time = scraper.toTime(meeting_datetime)

        # use regex to match pattern #/#/#; raise warning if no match

        # get event ID
        if type(event[scraper.event_info_key]) is dict:
            url = detail_info["url"]
            query_dict = parse_qs(urlparse(url).query)

            meeting_id = "legistar_{}_{}".format(
                self.legistar_instance, query_dict["ID"][0]
            )
        else:
            # No meeting details, e.g., event is in future
            url = None
            meeting_id = None

        return {
            "committee_name": self._event_name(event),
            "place": None,
            "state_or_province": None,
            "meeting_date": dtz_to_dt(meeting_time),
            "meeting_time": meeting_time,
            "meeting_id": meeting_id,
            "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
        }

    def _event_name(self, event):
        try:
            return event["Name"]["label"]
        except (KeyError, TypeError):
            return event["Name"]

    def _skippable(self, asset, start_date, end_date, file_size=None, download=False):
        start = parse_date(start_date)
        end = parse_date(end_date)
        # Use a generic (non-timezone aware) date for filtering
        meeting_date = dtz_to_dt(asset.meeting_date)
        # Skip if document URL is not available
        try:
            if not asset.url.startswith("http"):
                return True
        except AttributeError:
            return True
        # Skip if meeting date isn't between/equal to start and end dates
        if not start <= meeting_date <= end:
            return True
        # Add Content Type and Length when download specified
        if download:
            self._add_file_meta(asset)
        # if file_size and download are given, then check byte count
        if file_size and download:
            max_bytes = mb_to_bytes(file_size)
            if float(asset.content_length) > max_bytes:
                return True
        return False

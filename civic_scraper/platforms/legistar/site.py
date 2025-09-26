import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import logging
import warnings

import requests
from .events import (
    LegistarEventsScraper,
)  # Use local import to avoid stale dependencies

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.utils import parse_date, dtz_to_dt, mb_to_bytes, today_local_str

logger = logging.getLogger(__name__)


class Site(base.Site):
    """Legistar platform implementation."""

    def __init__(
        self,
        url,
        place=None,
        state_or_province=None,
        cache=None,
        parser_kls=None,
        committee_id=None,
        timezone=None,
        **kwargs,
    ):
        """Initialize Legistar site.

        Args:
            url (str): Base URL for the Legistar site
            place (str, optional): Name of the place/municipality
            state_or_province (str, optional): State or province
            cache (Cache, optional): Cache instance
            parser_kls (class, optional): Parser class
            committee_id (str, optional): Not used for Legistar
            timezone (str, optional): Timezone for dates
        """
        # Handle deprecated parameters for backward compatibility
        if "base_url" in kwargs:
            warnings.warn(
                "The base_url parameter is deprecated, use url instead",
                DeprecationWarning,
                stacklevel=2,
            )
            url = kwargs.pop("base_url")

        # Handle event_info_keys parameter
        event_info_keys = kwargs.get(
            "event_info_keys",
            {
                "meeting_details_info": "Meeting Details",
                "meeting_date_info": "Meeting Date",
                "meeting_time_info": "Meeting Time",
                "meeting_location_info": "Meeting Location",
            },
        )

        # Initialize base class with standardized parameters
        super().__init__(
            url=url,
            place=place,
            state_or_province=state_or_province,
            cache=cache or Cache(),
            parser_kls=parser_kls,
            committee_id=committee_id,
            timezone=timezone,
        )

        self.event_info_keys = event_info_keys

    def _init_platform_specific(self):
        """Initialize Legistar-specific attributes."""
        self.legistar_instance = urlparse(self.url).netloc.split(".")[0]

    def scrape(
        self,
        start_date=None,
        end_date=None,
        download=False,
        cache=False,
        file_size=None,
        asset_list=None,
    ):
        """Scrape a government website for metadata and/or docs.

        Args:
            start_date (str, optional): YYYY-MM-DD (default: current day)
            end_date (str, optional): YYYY-MM-DD (default: current day)
            download (bool, optional): Download file assets (default: False)
            cache (bool, optional): Cache source HTML (default: False) - not used in Legistar
            file_size (float, optional): Max size in MB to download (default: None)
            asset_list (list, optional): List of asset types to scrape (default: ["Agenda", "Minutes"])

        Returns:
            AssetCollection: Collection of scraped assets
        """
        if cache:
            logger.warning("Caching source HTML is not supported for Legistar platform")

        # Use default asset types if none provided
        asset_types = asset_list or ["Agenda", "Minutes"]

        # Use current day as default
        today = today_local_str()
        start = start_date or today
        end = end_date or today

        # Configure and instantiate the LegistarEventsScraper
        webscraper = LegistarEventsScraper(
            event_info_key=self.event_info_keys["meeting_details_info"],
            retry_attempts=3,
        )

        # Required to instantiate webscraper
        webscraper.BASE_URL = urlparse(self.url).netloc
        webscraper.EVENTSPAGE = self.url
        webscraper.TIMEZONE = self.timezone
        webscraper.date_format = "%m/%d/%Y %I:%M %p"

        # Scrape events
        assets = AssetCollection()
        start_year = int(start[:4])
        events = [event[0] for event in webscraper.events(since=start_year)]

        for event in events:

            meeting_meta = self._extract_meeting_meta(event, webscraper)
            for asset_type in asset_types:
                # Skip if a dictionary containing 'url' key is not present for the given asset type
                try:
                    asset = self._create_asset(event, meeting_meta, asset_type)
                except TypeError:
                    continue
                # Apply date and other filters
                if self._skippable_event(
                    asset, start, end, file_size=file_size, download=download
                ):
                    continue
                assets.append(asset)

        # Download assets if requested
        if download:
            self._download_assets_with_session(
                assets, file_size, asset_types, webscraper
            )

        return assets

    def _download_assets_with_session(
        self,
        assets: AssetCollection,
        file_size: float = None,
        asset_list: list = None,
        session=None,
    ) -> None:
        """Download assets using an existing session.

        Args:
            assets: AssetCollection to download from
            file_size: Maximum file size in MB to download
            asset_list: List of asset types to download
            session: Session object to use for downloading
        """
        asset_dir = Path(self.cache.path, "assets")
        asset_dir.mkdir(parents=True, exist_ok=True)

        for asset in assets:
            if self._skippable(asset, file_size, asset_list):
                continue
            if asset.url:
                dir_str = str(asset_dir)
                asset.download(target_dir=dir_str, session=session)

    def _add_file_meta(self, asset):
        """Add content-type and content-length to asset.

        Args:
            asset: Asset to add metadata to
        """
        headers = requests.head(asset.url, allow_redirects=True).headers
        asset.content_type = headers.get("content-type")
        asset.content_length = headers.get("content-length")

    def _create_asset(self, event, meeting_meta, asset_type):
        """Create an asset from an event.

        Args:
            event: Event data
            meeting_meta: Meeting metadata
            asset_type: Type of asset to create

        Returns:
            Asset: Created asset
        """
        # Check if the asset type is available
        if asset_type not in event:
            raise TypeError(f"Asset type '{asset_type}' not found in event data.")

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
            "place": self.place,
            "state_or_province": self.state_or_province,
        }
        kwargs.update(meeting_meta)
        return Asset(**kwargs)

    def _extract_meeting_meta(self, event, scraper):
        """Extract meeting metadata from event.

        Args:
            event: Event data
            scraper: Scraper instance

        Returns:
            dict: Meeting metadata
        """
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
            "meeting_date": dtz_to_dt(meeting_time),
            "meeting_time": meeting_time,
            "meeting_id": meeting_id,
            "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
        }

    def _event_name(self, event):
        """Extract event name.

        Args:
            event: Event data

        Returns:
            str: Event name
        """
        try:
            return event["Name"]["label"]
        except KeyError:
            # Fallback to a different key if "Name" is not present
            return event["Meeting Body"]
        except (KeyError, TypeError):
            return event["Name"]

    def _skippable_event(
        self, asset, start_date, end_date, file_size=None, download=False
    ):
        """Determine if an asset should be skipped.

        Args:
            asset: Asset to check
            start_date: Start date for filtering
            end_date: End date for filtering
            file_size: Maximum file size in MB
            download: Whether to download assets

        Returns:
            bool: True if asset should be skipped, False otherwise
        """
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
            max_bytes = self._mb_to_bytes(file_size)
            if float(asset.content_length) > max_bytes:
                return True
        return False

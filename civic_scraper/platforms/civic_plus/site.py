import datetime
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import warnings

import requests

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.utils import today_local_str

from .parser import Parser

logger = logging.getLogger(__name__)


class Site(base.Site):
    """CivicPlus site implementation."""

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
        """Initialize CivicPlus site.

        Args:
            url (str): Base URL for the CivicPlus site
            place (str, optional): Name of the place/municipality
            state_or_province (str, optional): State or province
            cache (Cache, optional): Cache instance
            parser_kls (class, optional): Parser class
            committee_id (str, optional): Not used for CivicPlus
            timezone (str, optional): Timezone for dates
        """
        # Handle deprecated parameters for backward compatibility
        if "place_name" in kwargs:
            warnings.warn(
                "The place_name parameter is deprecated, use place instead",
                DeprecationWarning,
                stacklevel=2,
            )
            place = kwargs.pop("place_name")

        # Extract state and subdomain from URL
        subdomain = urlparse(url).netloc.split(".")[0]
        extracted_state = self._get_asset_metadata(r"(?<=//)\w{2}(?=-)", url)
        extracted_place = self._get_asset_metadata(r"(?<=-)\w+(?=\.)", url)

        # Initialize base class with standardized parameters
        super().__init__(
            url=url,
            place=place or extracted_place,
            state_or_province=state_or_province or extracted_state,
            cache=cache,
            parser_kls=parser_kls or Parser,
            committee_id=committee_id,
            timezone=timezone,
        )

    def _init_platform_specific(self):
        """Initialize CivicPlus specific attributes."""
        self.subdomain = urlparse(self.url).netloc.split(".")[0]

    def scrape(
        self,
        start_date=None,
        end_date=None,
        cache=False,
        download=False,
        file_size=None,
        asset_list=None,
    ):
        """Scrape a government website for metadata and/or docs.

        Args:
            start_date (str, optional): YYYY-MM-DD (default: current day)
            end_date (str, optional): YYYY-MM-DD (default: current day)
            cache (bool, optional): Cache source HTML containing file metadata (default: False)
            download (bool, optional): Download file assets such as PDFs (default: False)
            file_size (float, optional): Max size in Megabytes of file assets to download
            asset_list (list, optional): List of asset types to limit scraping

        Returns:
            AssetCollection: A sequence of Asset instances
        """
        today = today_local_str()
        start = start_date or today
        end = end_date or today
        response_url, raw_html = self._search(start, end)

        # Cache the raw html from search results page
        if cache:
            cache_path = (
                f"{self.cache.artifacts_path}/{self._cache_page_name(response_url)}"
            )
            self.cache.write(cache_path, raw_html)
            logger.info(f"Cached search results page HTML: {cache_path}")

        file_metadata = self.parser_kls(raw_html).parse()
        assets = self._build_asset_collection(file_metadata)

        if download:
            self._download_assets(assets, file_size, asset_list)

        return assets

    def _cache_page_name(self, response_url):
        return (
            response_url.replace(":", "")
            .replace("//", "__")
            .replace("/", "__")
            .replace("?", "QUERY")
        )

    def _state_or_province(self, url):
        pass

    def _search(self, start_date, end_date):
        params = {
            "term": "",
            "CIDs": "all",
            "startDate": self._convert_date(start_date),
            "endDate": self._convert_date(end_date),
            "dateRange": "",
            "dateSelector": "",
        }
        # Search URLs follow the below pattern
        # /Search/?term=&CIDs=all&startDate=12/17/2020&endDate=12/18/2020&dateRange=&dateSelector=
        search_url = self.url.rstrip("/") + "/Search/"
        response = requests.get(search_url, params=params)
        return response.url, response.text

    def _convert_date(self, date_str):
        if date_str:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%m/%d/%Y")
        else:
            return None

    def _build_asset_collection(self, metadata):
        """Create assets from metadata

        Args:
            metadata (list) Array of dicts containing asset metadata.

        Returns:
            AssetCollection
        """
        assets = AssetCollection()
        for row in metadata:
            url = self._mk_url(self.url, row["url_path"])
            asset_args = {
                "state_or_province": self.state_or_province,
                "place": self.place,
                "committee_name": row["committee_name"],
                "meeting_id": self._mk_mtg_id(self.subdomain, row["meeting_id"]),
                "meeting_date": row["meeting_date"],
                "meeting_time": row["meeting_time"],
                "asset_name": row["meeting_title"],
                "asset_type": row["asset_type"],
                "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
                "url": url,
            }
            # TODO: Add conditional here to short-circuit
            # header request based on method option
            headers = requests.head(url, allow_redirects=True).headers
            asset_args.update(
                {
                    "content_type": headers["content-type"],
                    "content_length": headers.get("content-length", -1),
                }
            )
            assets.append(Asset(**asset_args))
        return assets

    def _mk_url(self, url, url_path):
        base_url = url.split("/Agenda")[0]
        return urljoin(base_url, url_path)

    def _mk_mtg_id(self, subdomain, raw_mtg_id):
        return f"civicplus_{subdomain}_{raw_mtg_id.lstrip('_')}"

    def _get_asset_metadata(self, regex, asset_link):
        """
        Extracts metadata from a provided asset URL.
        Input: Regex to extract metadata
        Returns: Extracted metadata as a string or "no_data" if no metadata is extracted
        """
        if re.search(regex, asset_link) is not None:
            return re.search(regex, asset_link).group(0)
        else:
            return "no_data"

    def _mb_to_bytes(self, size_mb):
        if size_mb is None:
            return None
        return float(size_mb) * 1048576

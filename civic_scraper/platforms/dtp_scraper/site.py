"""
Scraper for Digital TowPath NY sites (e.g. finetownny.gov)

For more information on the platform, see:
- https://www.digitaltownpath.com/ (main site)

"""

import logging
from datetime import datetime
from urllib.parse import urlparse

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.utils import today_local_str

from . import utils

logger = logging.getLogger(__name__)

# Hardcoded constants for finetownny.gov
PLACE = "fineny"
PLACE_NAME = "Fine New York"
STATE = "ny"

# Hardcoding supported sites since I am only aware of finetownny.gov using this platform.
# If we find more sites that use Digital TownPath, we can make this more dynamic.
SUPPORTED_SITES = "finetownny.gov"


class Site(base.Site):
    """Scraper for Digital TownPath sites (e.g. finetownny.gov)."""

    def __init__(self, base_url, cache=Cache()):
        """Initialize scraper.

        Args:
            base_url (str): Base URL of the Digital TownPath site (e.g. https://finetownny.gov)
            cache (Cache): Cache instance (default: new Cache())

        Currently only supports finetownny.gov, which is hardcoded in constants.
        """

        if not self.can_scrape(base_url):
            raise ValueError(
                f"Unsupported site: {base_url}. Supported sites: {SUPPORTED_SITES}"
            )

        super().__init__(base_url, cache=cache)
        self.base_url = base_url
        self.session = utils.create_session()

    @staticmethod
    def can_scrape(url: str) -> bool:
        """Determine if site can be scraped by this scraper."""
        return urlparse(url).netloc in SUPPORTED_SITES

    def scrape(self, start_date=None, end_date=None, cache=False, download=False):
        """Scrape the jurisdiction website for meeting documents.

        Args:
            start_date (str): YYYY-MM-DD format (default: today)
            end_date (str): YYYY-MM-DD format (default: today)
            cache (bool): Cache raw HTML (default: False)
            download (bool): Download PDF/doc files (default: False)

        Returns:
            AssetCollection: Collection of Asset instances

        The base URL should point to a Digital TownPath site root
        (e.g. https://finetownny.gov). The scraper navigates from
        {base_url}/meetings/meetings/ to discover categories, meetings,
        and documents.
        """
        # Use today as default dates
        today = today_local_str()
        start_date = start_date or today
        end_date = end_date or today

        ac = AssetCollection()
        processed_details = set()  # Track meeting detail IDs to avoid duplicates

        # Step 1: Get all categories (committees)
        try:
            categories = utils.get_categories(self.base_url, session=self.session)
            logger.info(f"Found {len(categories)} categories")
        except Exception as e:
            logger.error(f"Failed to fetch categories: {e}")
            return ac

        # Step 2: For each category, fetch all meetings across all years in the date range
        for category in categories:
            category_name = category["name"]
            logger.info(f"Processing category: {category_name}")

            try:
                # Start with the current year from the category URL
                category_url = category["url"]
                meetings_to_process = [(category_url, category_name)]
                processed_urls = set()

                # Process this year and check for other years
                while meetings_to_process:
                    current_url, _ = meetings_to_process.pop(0)

                    # Avoid processing the same URL twice
                    if current_url in processed_urls:
                        continue
                    processed_urls.add(current_url)

                    # Get meetings and soup in one request
                    try:
                        meetings, soup = utils.get_meetings_for_category_year(
                            current_url, session=self.session
                        )
                        logger.debug(f"Found {len(meetings)} meetings at {current_url}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch meetings for {current_url}: {e}"
                        )
                        continue

                    # Process each meeting
                    for meeting in meetings:
                        if meeting["detail_id"] in processed_details:
                            continue
                        processed_details.add(meeting["detail_id"])
                        try:
                            asset_count = self._process_meeting(
                                meeting,
                                category_name,
                                start_date,
                                end_date,
                                ac,
                            )
                            logger.debug(
                                f"Added {asset_count} assets from meeting {meeting['detail_id']}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to process meeting {meeting['detail_id']}: {e}"
                            )
                            continue

                    # Extract other years from the same soup (no extra request)
                    try:
                        other_years = utils.get_other_years_from_soup(soup)
                        for year_info in other_years:
                            year_url = year_info["url"]
                            if year_url not in processed_urls:
                                meetings_to_process.append((year_url, category_name))
                    except Exception as e:
                        logger.debug(
                            f"Failed to extract other years for {current_url}: {e}"
                        )
                        continue

            except Exception as e:
                logger.error(f"Failed to process category {category_name}: {e}")
                continue

        logger.info(f"Scraping complete. Found {len(ac)} total assets")
        return ac

    def _process_meeting(self, meeting, category_name, start_date, end_date, ac):
        """Process a single meeting and add assets to collection.

        Args:
            meeting (dict): Meeting info from utils.get_meetings_for_category_year()
            category_name (str): Committee/category name
            start_date (str): YYYY-MM-DD format
            end_date (str): YYYY-MM-DD format
            ac (AssetCollection): Collection to add assets to

        Returns:
            int: Number of assets added
        """
        detail_url = meeting["url"]
        detail_id = meeting["detail_id"]

        # Fetch meeting details
        meeting_details = utils.get_meeting_details(detail_url, session=self.session)

        # Check if meeting date is in range
        meeting_date = meeting_details.get("meeting_date")
        if not meeting_date:
            logger.warning(f"No meeting date for {detail_id}")
            return 0

        # Parse dates for comparison
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid date format: {start_date} or {end_date}")
            return 0

        if not (start_dt <= meeting_date <= end_dt):
            logger.debug(f"Meeting {detail_id} ({meeting_date}) outside date range")
            return 0

        asset_count = 0

        # Create an asset for each document (agenda, minutes)
        for doc in meeting_details.get("documents", []):
            doc_type = doc["type"]
            doc_url = doc["url"]

            # Create meeting ID
            meeting_id = f"{PLACE}-{meeting_date}-{detail_id}"

            # Create asset name
            asset_name = f"{meeting_details.get('meeting_title', 'Meeting')} - {doc_type.capitalize()}"

            # Get file metadata via session (reuses cookies/headers)
            content_type = None
            content_length = None
            try:
                response = self.session.head(doc_url, allow_redirects=True, timeout=10)
                content_type = response.headers.get("content-type")
                content_length = response.headers.get("content-length")
            except Exception as e:
                logger.warning(f"Failed to get headers for {doc_url}: {e}")

            # Create datetime object for meeting
            meeting_datetime = utils.parse_meeting_datetime(
                meeting_date, meeting_details.get("meeting_time")
            )

            # Create asset
            asset = Asset(
                url=doc_url,
                asset_type=doc_type,
                asset_name=asset_name,
                committee_name=meeting_details.get("committee_name") or category_name,
                place=PLACE,
                place_name=PLACE_NAME,
                state_or_province=STATE,
                meeting_date=meeting_datetime,
                meeting_id=meeting_id,
                scraped_by=civic_scraper.__version__,
                content_type=content_type,
                content_length=content_length,
            )

            ac.append(asset)
            asset_count += 1

        return asset_count

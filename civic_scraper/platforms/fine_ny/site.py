"""
Scraper for fine_ny

Base URL: https://finetownny.gov/categories
"""

import logging
from datetime import datetime
from pathlib import Path

import requests

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.utils import today_local_str

from . import utils

logger = logging.getLogger(__name__)

# Hardcoded constants for Fine NY
PLACE = "fineny"
PLACE_NAME = "Fine New York"
STATE = "ny"
BASE_MEETINGS_URL = "https://finetownny.gov"


class Site(base.Site):
    """Scraper for fine_ny."""

    def __init__(self, base_url, cache=Cache()):
        """Initialize scraper.

        Args:
            base_url (str): Base URL of the jurisdiction website (ignored; always uses https://finetownny.gov)
            cache (Cache): Cache instance (default: new Cache())
        """
        super().__init__(BASE_MEETINGS_URL, cache=cache)
        self.base_url = BASE_MEETINGS_URL

    def scrape(self, start_date=None, end_date=None, cache=False, download=False):
        """Scrape the jurisdiction website for meeting documents.

        Args:
            start_date (str): YYYY-MM-DD format (default: today)
            end_date (str): YYYY-MM-DD format (default: today)
            cache (bool): Cache raw HTML (default: False)
            download (bool): Download PDF/doc files (default: False)

        Returns:
            AssetCollection: Collection of Asset instances

        Approach:

        Implement Scraper.scraper method for the town of Fine, New York.
        * No matter what URL parameter is supplied always use https://finetownny.gov/categories
        as the base_url
        * Implement logic as testable functions in a utils/ module, and write tests for each function
        * Break logic further into helper functions as necessary.
        * Some Asset properties will always be the same and can be hardcoded:
          * Always use "ny" as the state_or_provice
          * Always use "Fine NY" as the place_name
          * Always use "fineny" as the place

        * The base URL contains a list of links to "categories" which correspond to committees.
        * Each committee link has a URL like https://finetownny.gov/meetings/meetings/Town%20Board/2026,
        * Each committee page contains a list of meetings for a given year (ex: 2026) and contains a
          list of other years that are structured the same way as this page.
        * Each meeting link listed on a committee page links to a meeting detail page
        * Each meeting detail page may or may not contain a link to one or more agenda PDFs
        * Each meeting detail page may or may not contain a link to one or more meeting minutes PDFs
        * Each agenda or minutes PDF should be represented as an Assset in the AssetCollection returned
          by the scrape() method.
        * The detail page URL will be like https://finetownny.gov/meetings/detail/30. The "30" we will extract
          as a detail_id to be used as part of the Asset.meeting_id
        * On the meeting detail page, you can obtain the following Asset properties. I'll include examples
            from the HTML.
            url (str): link to PDF
            asset_name (str): Example: February Regular Town Board Meeting from <h3 class="dtp-meeting-title">February Regular Town Board Meeting</h3>
            committee_name (str): Ex: Town Board from <h2 class="title dtp-meeting-category">Town Board</h2>
            place (str): Always "fineny"
            place_name (str): Always "Fine New York"
            state_or_province (str): Always "ny"
            asset_type (str): One of SUPPORTED_ASSET_TYPES. Ex: agenda
            meeting_date (datetime.datetime): Ex: 2026-02-11 from <time datetime="2026-02-11">February 11, 2026, 6:30 pm</time>
            meeting_time (datetime.time): Ex: 6:30 pm from <time datetime="2026-02-11">February 11, 2026, 6:30 pm</time>
            meeting_id (str): Ex: fineny-{date}-{detail_id}
            scraped_by (str): civic_scraper.__version__
            content_type (str): File type of the asset as given by HTTP headers. Ex: 'application/pdf'
            content_length (str): Asset size in bytes
        """
        # Use today as default dates
        today = today_local_str()
        start_date = start_date or today
        end_date = end_date or today

        ac = AssetCollection()

        # Step 1: Get all categories (committees)
        try:
            categories = utils.get_categories(self.base_url)
            logger.info(f"Found {len(categories)} categories")
        except Exception as e:
            logger.error(f"Failed to fetch categories: {e}")
            return ac

        # Step 2: For each category, fetch all meetings across all years in the date range
        for category in categories:
            category_name = category['name']
            logger.info(f"Processing category: {category_name}")

            try:
                # Start with the current year from the category URL
                category_url = category['url']
                meetings_to_process = [(category_url, category_name)]
                processed_urls = set()

                # Process this year and check for other years
                while meetings_to_process:
                    current_url, _ = meetings_to_process.pop(0)

                    # Avoid processing the same URL twice
                    if current_url in processed_urls:
                        continue
                    processed_urls.add(current_url)

                    # Get meetings for this category/year
                    try:
                        meetings = utils.get_meetings_for_category_year(current_url)
                        logger.debug(f"Found {len(meetings)} meetings at {current_url}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch meetings for {current_url}: {e}")
                        continue

                    # Process each meeting
                    for meeting in meetings:
                        try:
                            asset_count = self._process_meeting(
                                meeting,
                                category_name,
                                start_date,
                                end_date,
                                ac,
                                download
                            )
                            logger.debug(f"Added {asset_count} assets from meeting {meeting['detail_id']}")
                        except Exception as e:
                            logger.warning(f"Failed to process meeting {meeting['detail_id']}: {e}")
                            continue

                    # Get other years for this category
                    try:
                        other_years = utils.get_other_years(current_url)
                        for year_info in other_years:
                            year_url = year_info['url']
                            if year_url not in processed_urls:
                                meetings_to_process.append((year_url, category_name))
                    except Exception as e:
                        logger.debug(f"Failed to fetch other years for {current_url}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Failed to process category {category_name}: {e}")
                continue

        logger.info(f"Scraping complete. Found {len(ac)} total assets")
        return ac

    def _process_meeting(self, meeting, category_name, start_date, end_date, ac, download):
        """Process a single meeting and add assets to collection.

        Args:
            meeting (dict): Meeting info from utils.get_meetings_for_category_year()
            category_name (str): Committee/category name
            start_date (str): YYYY-MM-DD format
            end_date (str): YYYY-MM-DD format
            ac (AssetCollection): Collection to add assets to
            download (bool): Whether to download files

        Returns:
            int: Number of assets added
        """
        detail_url = meeting['url']
        detail_id = meeting['detail_id']

        # Fetch meeting details
        meeting_details = utils.get_meeting_details(detail_url)

        # Check if meeting date is in range
        meeting_date = meeting_details.get('meeting_date')
        if not meeting_date:
            logger.warning(f"No meeting date for {detail_id}")
            return 0

        # Parse dates for comparison
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {start_date} or {end_date}")
            return 0

        if not (start_dt <= meeting_date <= end_dt):
            logger.debug(f"Meeting {detail_id} ({meeting_date}) outside date range")
            return 0

        asset_count = 0

        # Create an asset for each document (agenda, minutes)
        for doc in meeting_details.get('documents', []):
            doc_type = doc['type']
            doc_url = doc['url']

            # Create meeting ID
            meeting_id = f"{PLACE}-{meeting_date}-{detail_id}"

            # Create asset name
            asset_name = f"{meeting_details.get('meeting_title', 'Meeting')} - {doc_type.capitalize()}"

            # Get file metadata
            content_type = None
            content_length = None
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.head(doc_url, headers=headers, allow_redirects=True, timeout=10)
                content_type = response.headers.get('content-type')
                content_length = response.headers.get('content-length')
            except Exception as e:
                logger.warning(f"Failed to get headers for {doc_url}: {e}")

            # Create datetime object for meeting
            meeting_datetime = utils.parse_meeting_datetime(
                meeting_date,
                meeting_details.get('meeting_time')
            )

            # Create asset
            asset = Asset(
                url=doc_url,
                asset_type=doc_type,
                asset_name=asset_name,
                committee_name=meeting_details.get('committee_name') or category_name,
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

            # Download if requested
            if download:
                try:
                    asset_dir = Path(self.cache.path, "assets")
                    asset_dir.mkdir(parents=True, exist_ok=True)
                    asset.download(target_dir=str(asset_dir))
                    logger.debug(f"Downloaded {doc_url}")
                except Exception as e:
                    logger.warning(f"Failed to download {doc_url}: {e}")

        return asset_count

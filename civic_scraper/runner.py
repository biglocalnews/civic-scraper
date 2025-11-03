import importlib
import logging
import re
from urllib.parse import urlparse

from civic_scraper.base.asset import AssetCollection
from civic_scraper.base.cache import Cache

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    pass


class Runner:
    """
    Facade class to simplify invocation and usage of scrapers.

    Arguments:

    - cache_path -- Path to cache location for scraped file artifact

    """

    def __init__(self, cache_path=None):
        self.cache_path = cache_path

    def scrape(
        self,
        start_date,
        end_date,
        site_urls=[],
        cache=False,
        download=False,
        file_size=None,
        asset_list=None,
    ):
        """Scrape file metadata and assets for a list of agency sites.

        For a given scraper, scrapes file artificate metadata and
        downloads file artificats. Automatically generats a metadata
        CSV of file assets.

        If requested, caches intermediate file artifacts such as HTML
        from scraped pages and downloads file assets such as agendas, minutes
        (caching and downloading are optional and are off by default).

        Args:

            start_date (str): Start date of scrape (YYYY-MM-DD)
            end_date (str): End date of scrape (YYYY-MM-DD)
            site_urls (list): List of site URLs
            cache (bool): Optionally cache intermediate file artificats such as HTML
                (default: False)
            download (bool): Optionally download file assets such as agendas (default: False)
            file_size (float, optional): Maximum file size in MB to download
            asset_list (list, optional): List of asset types to limit scraping

        Outputs:
            Metadata CSV listing file assets for given sites and params.

        Returns:
            AssetCollection instance
        """
        asset_collection = AssetCollection()
        cache_obj = Cache(self.cache_path)
        logger.info(
            f"Scraping {len(site_urls)} site(s) from {start_date} to {end_date}..."
        )
        for url in site_urls:
            try:
                SiteClass = self._get_site_class(url)

                # Extract place and state/province from URL if possible
                place, state_or_province = self._extract_location_from_url(url)

                # Initialize site with standardized parameters
                site = SiteClass(
                    url=url,
                    place=place,
                    state_or_province=state_or_province,
                    cache=cache_obj if cache else None,
                )

                logger.info(f"\tScraping {url}")

                # Call scrape with standardized parameters
                _collection = site.scrape(
                    start_date=start_date,
                    end_date=end_date,
                    cache=cache,
                    download=download,
                    file_size=file_size,
                    asset_list=asset_list,
                )

                asset_collection.extend(_collection)
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue

        metadata_file = asset_collection.to_csv(cache_obj.metadata_files_path)
        logger.info(f"Wrote asset metadata CSV: {metadata_file}")

        logger.info(f"Found {len(asset_collection)} asset(s)")

        return asset_collection

    def _get_site_class(self, url):
        """Get the appropriate site class based on URL patterns."""
        class_name = self._get_site_class_name(url)

        # Map class names to module paths
        class_to_module = {
            "CivicPlusSite": "civic_scraper.platforms.civic_plus.site",
            "GranicusSite": "civic_scraper.platforms.granicus.site",
            "BoardDocsSite": "civic_scraper.platforms.boarddocs.site",
            "LegistarSite": "civic_scraper.platforms.legistar.site",
        }

        if class_name not in class_to_module:
            raise ScraperError(f"Unsupported site type: {class_name}")

        # Import the module and get the Site class
        module_path = class_to_module[class_name]
        module = importlib.import_module(module_path)

        return module.Site

    def _get_site_class_name(self, url):
        """Determine the class name based on URL patterns."""
        if re.search(r"(civicplus|AgendaCenter)", url):
            return "CivicPlusSite"
        elif re.search(r"(granicus|granicusid)", url):
            return "GranicusSite"
        elif re.search(r"boarddocs", url):
            return "BoardDocsSite"
        elif re.search(r"legistar", url):
            return "LegistarSite"
        else:
            raise ScraperError(f"Could not determine site type from URL: {url}")

    def _extract_location_from_url(self, url):
        """
        Extract place and state/province from URL if possible.

        Args:
            url: Site URL

        Returns:
            tuple: (place, state_or_province)
        """
        place = None
        state_or_province = None

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # CivicPlus pattern: ca-cityname.civicplus.com
        civicplus_match = re.search(r"([a-z]{2})-([a-z]+)\.civicplus", domain)
        if civicplus_match:
            state_or_province = civicplus_match.group(1)
            place = civicplus_match.group(2)

        # BoardDocs pattern: go.boarddocs.com/ca/cityname
        boarddocs_match = re.search(r"boarddocs\.com/([a-z]{2})/([a-z]+)", url)
        if boarddocs_match:
            state_or_province = boarddocs_match.group(1)
            place = boarddocs_match.group(2)

        return place, state_or_province

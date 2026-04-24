import importlib
import logging
import re
from typing import Optional

from civic_scraper.base.asset import AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.platforms import DigitalTowPathSite

logger = logging.getLogger(__name__)


class DownloadResult:
    def __init__(self):
        self.successful = []
        self.failed = []


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
            SiteClass = self._get_site_class(url)
            kwargs = {}
            if cache:
                kwargs["cache"] = cache_obj
            site = SiteClass(url, **kwargs)
            logger.info(f"\t{url}")
            _collection = site.scrape(
                start_date,
                end_date,
                cache=cache,
            )
            asset_collection.extend(_collection)
        metadata_file = asset_collection.to_csv(cache_obj.metadata_files_path)
        logger.info(f"Wrote asset metadata CSV: {metadata_file}")
        return asset_collection

    def download_assets(
        self,
        assets: AssetCollection,
        target_dir: Optional[str] = None,
        file_size_limit: Optional[float] = None,
        asset_types: Optional[list[str]] = None,
    ) -> DownloadResult:
        """Download assets with filtering and error handling."""
        if not target_dir:
            cache_obj = Cache(self.cache_path)
            target_dir = cache_obj.assets_path

        result = DownloadResult()

        logger.info(f"Evaluating {len(assets)} asset(s) for download...")
        for asset in assets:
            if asset_types and asset.asset_type not in asset_types:
                continue

            if file_size_limit is not None and asset.content_length:
                try:
                    size_mb = int(asset.content_length) / (1024 * 1024)
                    if size_mb > file_size_limit:
                        continue
                except ValueError:
                    pass

            logger.info(f"	Downloading {asset.url}")
            download_path = asset.download(target_dir)
            if download_path:
                result.successful.append(asset)
            else:
                result.failed.append(asset)

        return result

    def _get_site_class(self, url):
        class_name = self._get_site_class_name(url)
        target_module = "civic_scraper.platforms"
        mod = importlib.import_module(target_module)
        return getattr(mod, class_name)

    def _get_site_class_name(self, url):
        if re.search(r"(civicplus|AgendaCenter)", url):
            return "CivicPlusSite"
        # TODO: Discuss whether we want to elevate this pattern for all scrapers
        # then we can just iterate through all scrapers and call can_scrape on each
        if DigitalTowPathSite.can_scrape(url):
            return "DigitalTowPathSite"
        raise ScraperError(f"No scraper found for {url}")

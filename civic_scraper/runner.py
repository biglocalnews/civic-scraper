import importlib
import logging
import re

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
        if download:
            download_counter = 0
            logger.info(
                f"Downloading {len(asset_collection)} file asset(s) to {cache_obj.assets_path}..."
            )
            for asset in asset_collection:
                # TODO: Add error-handling here
                logger.info(f"\t{asset.url}")
                asset.download(cache_obj.assets_path)
                download_counter += 1
        return asset_collection

    def _get_site_class(self, url):
        class_name = self._get_site_class_name(url)
        target_module = "civic_scraper.platforms"
        mod = importlib.import_module(target_module)
        return getattr(mod, class_name)

    def _get_site_class_name(self, url):
        if re.search(r"(civicplus|AgendaCenter)", url):
            return "CivicPlusSite"

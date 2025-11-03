import datetime
from typing import Optional, List, Union, Dict, Any
from pathlib import Path

from .asset import AssetCollection, Asset
from .cache import Cache


class Site:
    """Base class for all Site scrapers.

    Args:
        url (str): URL to a government agency site
        place (str, optional): Name of the place/municipality
        state_or_province (str, optional): State or province
        cache (Cache instance, optional): Cache instance
            (default: ".civic-scraper" in user home dir)
        parser_kls (class, optional): Parser class to extract
            data from government agency websites.
        committee_id (str, optional): ID of committee to scrape
        timezone (str, optional): Timezone for dates
    """

    def __init__(
        self,
        url: str,
        place: Optional[str] = None,
        state_or_province: Optional[str] = None,
        cache: Optional[Cache] = None,
        parser_kls=None,
        committee_id: Optional[str] = None,
        timezone: Optional[str] = "US/Eastern",
    ):
        self.runtime = datetime.datetime.utcnow().date()
        self.url = url
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache or Cache()
        self.parser_kls = parser_kls
        self.committee_id = committee_id
        self.timezone = timezone

        # Platform-specific initialization
        self._init_platform_specific()

    def _init_platform_specific(self):
        """Platform-specific initialization. Override in subclasses."""
        pass

    def scrape(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        download: bool = False,
        cache: bool = False,
        file_size: Optional[float] = None,
        asset_list: Optional[List[str]] = None,
    ) -> AssetCollection:
        """Scrape a government website for metadata and/or docs.

        Args:
            start_date (str, optional): YYYY-MM-DD start date (default: today)
            end_date (str, optional): YYYY-MM-DD end date (default: today)
            download (bool, optional): Download file assets (default: False)
            cache (bool, optional): Cache source HTML (default: False)
            file_size (float, optional): Max size in MB of files to download
            asset_list (list, optional): List of asset types to limit scraping

        Returns:
            AssetCollection: Collection of scraped assets
        """
        raise NotImplementedError

    def _download_assets(
        self,
        assets: AssetCollection,
        file_size: Optional[float] = None,
        asset_list: Optional[List[str]] = None,
    ) -> None:
        """Download assets based on filter criteria.

        Args:
            assets: AssetCollection to download from
            file_size: Maximum file size in MB to download
            asset_list: List of asset types to download
        """
        asset_dir = Path(self.cache.path, "assets")
        asset_dir.mkdir(parents=True, exist_ok=True)

        for asset in assets:
            if self._skippable(asset, file_size, asset_list):
                continue
            asset.download(str(asset_dir))

    def _skippable(
        self, asset: Asset, file_size: Optional[float], asset_list: Optional[List[str]]
    ) -> bool:
        """Determine if asset should be skipped during download.

        Args:
            asset: Asset to check
            file_size: Max file size in MB
            asset_list: List of asset types to include

        Returns:
            True if asset should be skipped, False otherwise
        """
        if file_size and asset.size_mb and asset.size_mb > file_size:
            return True

        if asset_list and asset.asset_type not in asset_list:
            return True

        return False

    def _mb_to_bytes(self, size_mb: Optional[float]) -> Optional[float]:
        """Convert MB to bytes.

        Args:
            size_mb: Size in megabytes

        Returns:
            Size in bytes or None if input is None
        """
        if size_mb is None:
            return None
        return float(size_mb) * 1048576

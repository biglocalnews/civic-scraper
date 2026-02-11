"""
Tests for fine_ny scraper

Run with: pipenv run pytest -sv tests/test_fine_ny_site.py
"""

import datetime
import pytest

from civic_scraper.platforms.fine_ny import FineNySite


@pytest.mark.vcr()
def test_scrape_defaults(civic_scraper_dir, set_default_env):
    """Test basic scraping functionality with defaults.

    On first run: VCR records HTTP interactions to cassette
    On subsequent runs: VCR replays mocked responses
    """
    site = FineNySite("https://finetownny.gov/categories/")
    assets = site.scrape()

    # Based on VCR recording on Feb. 11, 2026, there should be exactly 1 asset
    assert len(assets) == 1, "Should find exactly 1 asset"

    # Verify result type
    assert hasattr(assets, '__iter__'), "Assets should be iterable"

    # Verify first asset has required fields
    asset = assets[0]
    assert asset.url.startswith("https://"), "URL should be absolute"
    assert asset.asset_type in ["agenda", "minutes", "other"], "Asset type should be recognized"
    assert isinstance(asset.meeting_date, datetime.datetime), "Meeting date should be datetime"


@pytest.mark.vcr()
def test_scrape_with_date_range(civic_scraper_dir, set_default_env):
    """Test scraping with specific date range.
    """
    site = FineNySite("https://finetownny.gov/categories/")
    start_date = "2026-01-01"  # Same as test meeting date
    end_date = "2026-02-05"

    assets = site.scrape(start_date=start_date, end_date=end_date)

    # Based on VCR recording on Feb. 11, 2026, there should be exactly 2 assets
    assert len(assets) == 2, "Should find exactly 2 assets in the date range"


@pytest.mark.vcr()
def test_site_initialization():
    """Test Site can be initialized."""
    site = FineNySite("https://finetownny.gov/categories/")

    # Fine NY always uses the same base URL regardless of what's passed in
    assert site.base_url == "https://finetownny.gov"
    assert site.url == "https://finetownny.gov"

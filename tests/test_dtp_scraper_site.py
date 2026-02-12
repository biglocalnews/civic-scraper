"""
Tests for DTP scraper

Run with: pipenv run pytest -sv tests/test_dtp_scraper_site.py
"""

import datetime
from unittest.mock import patch

import pytest

from civic_scraper.platforms.dtp_scraper import DtpScraperSite

# The VCR cassettes were recorded on this date. When scrape() is called
# without explicit dates it defaults to "today", which must match the
# cassette data. If cassettes are re-recorded, update this value.
_CASSETTE_DATE = "2026-02-11"


@pytest.fixture(autouse=True)
def _pin_today():
    """Pin today_local_str() to the cassette recording date.

    Without this, scrape() defaults to the real current date, which
    won't match meetings in the cassettes and tests will fail.
    """
    with patch(
        "civic_scraper.platforms.dtp_scraper.site.today_local_str",
        return_value=_CASSETTE_DATE,
    ):
        yield


@pytest.mark.vcr()
def test_scrape_defaults(civic_scraper_dir, set_default_env):
    """Test basic scraping functionality with defaults.

    On first run: VCR records HTTP interactions to cassette
    On subsequent runs: VCR replays mocked responses
    """
    site = DtpScraperSite("https://finetownny.gov/categories/")
    assets = site.scrape()

    # Based on VCR recording on Feb. 12, 2026, there should be exactly 1 asset
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
    site = DtpScraperSite("https://finetownny.gov/categories/")
    start_date = "2026-01-01"  # Same as test meeting date
    end_date = "2026-02-05"

    assets = site.scrape(start_date=start_date, end_date=end_date)

    # Based on VCR recording on Feb. 12, 2026, there should be exactly 2 assets
    assert len(assets) == 2, "Should find exactly 2 assets in the date range"


@pytest.mark.vcr()
def test_site_initialization():
    """Test Site can be initialized."""
    site = DtpScraperSite("https://finetownny.gov/categories/")

    # DTP scraper uses whatever base URL is passed in
    assert site.base_url == "https://finetownny.gov/categories/"
    assert site.url == "https://finetownny.gov/categories/"

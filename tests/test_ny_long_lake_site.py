"""
Tests for ny_long_lake scraper

Run with: pipenv run pytest -sv tests/test_ny_long_lake_site.py
"""

import datetime
import pytest

from civic_scraper.platforms.ny_long_lake import NyLongLakeSite


@pytest.mark.vcr()
def test_scrape_defaults(civic_scraper_dir, set_default_env):
    """Test basic scraping functionality with defaults.

    On first run: VCR records HTTP interactions to cassette
    On subsequent runs: VCR replays mocked responses

    TODO: Update the expected count based on what's actually on the website.
    Inspect https://www.mylonglake.com/agendas-minutes-announcements/ to count how many documents you expect to find,
    then replace the assertion below with the exact number.
    """
    site = NyLongLakeSite("https://www.mylonglake.com/agendas-minutes-announcements//")
    assets = site.scrape()

    # TODO: Replace X with the number of documents you expect to find
    # (e.g., if the website shows 3 agendas on the first page, use 3)
    assert len(assets) == X, "Should find exactly X assets (update X based on what's on the website)"

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

    TODO: Adjust dates and expected count based on your target website.
    """
    site = NyLongLakeSite("https://www.mylonglake.com/agendas-minutes-announcements//")
    start_date = "2024-01-01"
    end_date = "2024-01-31"

    assets = site.scrape(start_date=start_date, end_date=end_date)

    # TODO: Replace Y with the expected count for this date range
    assert len(assets) == Y, "Should find exactly Y assets in the date range"


@pytest.mark.vcr()
def test_site_initialization():
    """Test Site can be initialized."""
    site = NyLongLakeSite("https://www.mylonglake.com/agendas-minutes-announcements//")

    assert site.base_url == "https://www.mylonglake.com/agendas-minutes-announcements//"
    assert site.url == "https://www.mylonglake.com/agendas-minutes-announcements//"

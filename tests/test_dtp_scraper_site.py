"""
Tests for DTP scraper

Run with: pipenv run pytest -sv tests/test_dtp_scraper_site.py
"""

import datetime
from unittest.mock import patch

import pytest

from civic_scraper.platforms.dtp_scraper import DtpScraperSite

@pytest.mark.vcr()
def test_scrape_with_date_range(civic_scraper_dir, set_default_env):
    """Test scraping with specific date range."""
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

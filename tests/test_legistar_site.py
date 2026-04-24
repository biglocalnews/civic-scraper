import datetime
from unittest.mock import patch

import pytest
import pytz

from civic_scraper.base.cache import Cache
from civic_scraper.platforms import LegistarSite

_CASSETTE_NOW = datetime.datetime(2025, 6, 1, tzinfo=pytz.utc)


@pytest.fixture(autouse=True)
def _pin_legistar_year():
    with patch("legistar.base.LegistarScraper.now", return_value=_CASSETTE_NOW):
        yield


@pytest.mark.vcr()
def test_scrape_defaults():
    start_date = "2022-04-05"
    end_date = "2022-04-18"
    url = "https://nashville.legistar.com/Calendar.aspx"
    site = LegistarSite(url, timezone="US/Central")
    assets = site.scrape(start_date, end_date)
    assert len(assets) == 5


@pytest.mark.vcr()
def test_scrape_no_meetings_for_date():
    url = "https://nashville.legistar.com/Calendar.aspx"
    site = LegistarSite(url, timezone="US/Central")
    assets = site.scrape(start_date="2022-01-01", end_date="2022-01-01")
    assert assets == []


@patch(
    "civic_scraper.platforms.legistar.site.today_local_str", return_value="2022-04-05"
)
@pytest.mark.vcr()
def test_scrape_current_day_by_default(today_local_str, tmpdir):
    url = "https://nashville.legistar.com/Calendar.aspx"
    site = LegistarSite(url, cache=Cache(tmpdir), timezone="US/Central")
    assets = site.scrape()
    assert len(assets) > 0


@pytest.mark.vcr()
def test_multiyear_scrape(tmpdir):
    url = "https://nashville.legistar.com/Calendar.aspx"
    site = LegistarSite(url, cache=Cache(tmpdir), timezone="US/Central")
    assets = site.scrape(start_date="2021-12-21", end_date="2022-01-04")
    assert len(assets) == 4

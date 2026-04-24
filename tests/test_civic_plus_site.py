import datetime
from unittest.mock import patch

import pytest

from civic_scraper.base.cache import Cache
from civic_scraper.platforms import CivicPlusSite


@pytest.mark.vcr()
def test_scrape_defaults():
    start_date = "2020-05-03"
    end_date = "2020-05-06"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url)
    assets = cp.scrape(start_date, end_date)
    assert len(assets) >= 4
    agenda = [asset for asset in assets if asset.url.endswith("Agenda/_05052020-382")][
        0
    ]
    assert agenda.asset_type == "agenda"
    assert agenda.meeting_date == datetime.datetime(2020, 5, 5)


def test_place_name_arg():
    site_url = "https://ca-losaltoshills.civicplus.com/AgendaCenter"
    site = CivicPlusSite(site_url)
    assert site.place == "losaltoshills"


@pytest.mark.vcr()
def test_scrape_no_meetings_for_date():
    site_url = "https://nm-lascruces.civicplus.com/AgendaCenter"
    scrape_date = "2020-08-29"
    cp = CivicPlusSite(site_url)
    assets = cp.scrape(start_date=scrape_date, end_date=scrape_date)
    assert assets == []


@pytest.mark.vcr()
def test_scrape_cache_false_default(tmpdir):
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    cp.scrape("2020-05-03", "2020-05-06")
    assert [f.basename for f in tmpdir.listdir()] == []


@pytest.mark.vcr()
def test_scrape_cache_true(tmpdir):
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    cp.scrape("2020-05-03", "2020-05-06", cache=True)
    assert tmpdir.join("artifacts").exists()


@pytest.mark.vcr()
def test_scrape_place_state():
    site_url = "http://wi-columbus.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(site_url)
    assets = cp.scrape(start_date="2020-10-01", end_date="2020-10-09")
    assert assets[2].place == "columbus"


@patch(
    "civic_scraper.platforms.civic_plus.site.today_local_str", return_value="2020-05-05"
)
@pytest.mark.vcr()
def test_scrape_current_day_by_default(today_local_str, tmpdir):
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    assets = cp.scrape()
    assert len(assets) > 0

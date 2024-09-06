import datetime
from unittest.mock import patch

import pytest

from civic_scraper.base.cache import Cache
from civic_scraper.platforms import CivicPlusSite

from .conftest import file_contents


@pytest.mark.vcr()
def test_scrape_defaults():
    """
    Test default behavior of CivicPlus.scrape
    """
    start_date = "2020-05-03"
    end_date = "2020-05-06"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url)
    assets = cp.scrape(start_date, end_date)
    assert len(assets) >= 4
    agenda = [asset for asset in assets if asset.url.endswith("Agenda/_05052020-382")][
        0
    ]
    assert (
        agenda.url
        == "http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05052020-382"
    )
    assert agenda.committee_name == "Board of Commissioners"
    assert (
        agenda.asset_name == "May 5, 2020 Recessed Meeting/Budget Work Session Agenda"
    )
    assert agenda.place == "nashcounty"
    assert agenda.state_or_province == "nc"
    assert agenda.asset_type == "agenda"
    assert agenda.meeting_date == datetime.datetime(2020, 5, 5)
    assert agenda.meeting_time is None
    assert agenda.meeting_id == "civicplus_nc-nashcounty_05052020-382"
    assert agenda.scraped_by == "civic-scraper_0.1.0"
    assert agenda.content_type == "application/pdf"
    assert agenda.content_length == "19536"
    # Check that assets are in the correct date range
    expected_meeting_dates = [datetime.datetime(2020, 5, day) for day in range(3, 7)]
    for asset in assets:
        assert asset.meeting_date in expected_meeting_dates
    # Check range of asset types
    expected_asset_types = [
        "agenda",
        "minutes",
        "agenda",
        "minutes",
    ]
    actual_asset_types = [asset.asset_type for asset in assets]
    assert expected_asset_types == actual_asset_types


def test_place_name_arg():
    site_url = "https://ca-losaltoshills.civicplus.com/AgendaCenter"
    site = CivicPlusSite(site_url)
    # default
    assert site.place == "losaltoshills"
    assert site.place_name is None
    # Now test with the arg
    site2 = CivicPlusSite(site_url, place_name="Los Altos Hills")
    assert site2.place_name == "Los Altos Hills"


@pytest.mark.vcr()
def test_scrape_no_meetings_for_date():
    """
    Scrape should not return assets for dates with no meetings
    """
    site_url = "https://nm-lascruces.civicplus.com/AgendaCenter"
    scrape_date = "2020-08-29"
    cp = CivicPlusSite(site_url)
    assets = cp.scrape(start_date=scrape_date, end_date=scrape_date)
    assert assets == []


@pytest.mark.vcr()
def test_scrape_cache_false_default(tmpdir):
    "Scrape should not cache search results pages by default"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    start_date = "2020-05-03"
    end_date = "2020-05-06"
    cp.scrape(start_date, end_date)
    actual_files = [f.basename for f in tmpdir.listdir()]
    assert actual_files == []


@pytest.mark.vcr()
def test_scrape_cache_true(tmpdir):
    "Setting cache to True should trigger caching of search results page"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    start_date = "2020-05-03"
    end_date = "2020-05-06"
    cp.scrape(
        start_date,
        end_date,
        cache=True,
    )
    artifacts_path = tmpdir.join("artifacts")
    actual_files = [f.basename for f in artifacts_path.listdir()]
    expected = [
        (
            "http__nc-nashcounty.civicplus.com__AgendaCenter__Search__QUERY"
            "term=&CIDs=all&startDate=05%2F03%2F2020"
            "&endDate=05%2F06%2F2020&dateRange=&dateSelector="
        )
    ]
    assert actual_files == expected
    # Spot check contents
    inpath = artifacts_path.join(expected[0])
    contents = file_contents(inpath)
    assert "Board of Commissioners" in contents


@pytest.mark.vcr()
def test_scrape_download_default(tmpdir):
    "Scraper should not download file assets by default"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    start_date = "2020-05-05"
    end_date = "2020-05-05"
    cp.scrape(
        start_date,
        end_date,
    )
    target_dir = tmpdir.join("assets")
    assert not target_dir.exists()


@pytest.mark.vcr()
def test_scrape_download_true(tmpdir):
    "Setting download=True should download file assets"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    start_date = "2020-05-05"
    end_date = "2020-05-05"
    cp.scrape(
        start_date,
        end_date,
        download=True,
    )
    target_dir = tmpdir.join("assets")
    actual_files = {f.basename for f in target_dir.listdir()}
    expected = {
        "civicplus_nc-nashcounty_05052020-382_minutes.pdf",
        "civicplus_nc-nashcounty_05052020-382_agenda.pdf",
    }
    assert actual_files == expected


@pytest.mark.vcr()
def test_scrape_download_filter_size(tmpdir):
    "Downloads should be filterable by size in MB"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    start_date = "2020-05-05"
    end_date = "2020-05-05"
    # Byte sizes of two files for May 5, 2020
    # - Minutes/_05052020-382 = '28998'
    # - Agenda/_05052020-382 '19536'
    # 19536 bytes in agenda i.e. 0.0186309814453125  MBs
    cp.scrape(
        start_date,
        end_date,
        download=True,
        file_size=0.0186309814453125,
    )
    target_dir = tmpdir.join("assets")
    actual_files = [f.basename for f in target_dir.listdir()]
    expected = ["civicplus_nc-nashcounty_05052020-382_agenda.pdf"]
    assert actual_files == expected


@pytest.mark.vcr()
def test_scrape_download_filter_type(tmpdir):
    "Downloads should be filterable by type"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    start_date = "2020-05-05"
    end_date = "2020-05-05"
    cp.scrape(
        start_date,
        end_date,
        download=True,
        asset_list=["minutes"],
    )
    target_dir = tmpdir.join("assets")
    actual_files = [f.basename for f in target_dir.listdir()]
    expected = ["civicplus_nc-nashcounty_05052020-382_agenda.pdf"]
    assert actual_files == expected


@pytest.mark.vcr()
def test_scrape_download_filter_both(tmpdir):
    "Downloads should be filterable by type and file size"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    start_date = "2020-05-05"
    end_date = "2020-05-05"
    # Below, minutes will be filtered due to its size exceeding 0.01MB
    # *and* agenda, which is approx 0.018 MB will be filtered because
    # of asset_list
    cp.scrape(
        start_date,
        end_date,
        download=True,
        asset_list=["agenda"],
        file_size=0.019,
    )
    target_dir = tmpdir.join("assets")
    actual_files = [f.basename for f in target_dir.listdir()]
    assert actual_files == []


@pytest.mark.vcr()
def test_scrape_place_state():
    "Place should be correct on sites that redirect"
    site_url = "http://wi-columbus.civicplus.com/AgendaCenter"
    start_date = "2020-10-01"
    end_date = "2020-10-09"
    cp = CivicPlusSite(site_url)
    assets = cp.scrape(start_date=start_date, end_date=end_date)
    assert assets[2].state_or_province == "wi"
    assert assets[2].place == "columbus"


@patch(
    "civic_scraper.platforms.civic_plus.site.today_local_str", return_value="2020-05-05"
)
@pytest.mark.vcr()
def test_scrape_current_day_by_default(today_local_str, tmpdir):
    "Scrape should assume current day be default"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    cp = CivicPlusSite(url, cache=Cache(tmpdir))
    cp.scrape(download=True)
    target_dir = tmpdir.join("assets")
    actual_files = {f.basename for f in target_dir.listdir()}
    expected = {
        "civicplus_nc-nashcounty_05052020-382_minutes.pdf",
        "civicplus_nc-nashcounty_05052020-382_agenda.pdf",
    }
    assert actual_files == expected

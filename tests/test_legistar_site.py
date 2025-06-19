import datetime
from unittest.mock import patch

import pytest
import pytz

from civic_scraper.base.cache import Cache
from civic_scraper.platforms import LegistarSite


# TODO: Bring back tests (remove skip decorator) when python-lesistar-scraper is resolved.
@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@pytest.mark.vcr()
def test_scrape_defaults():
    """
    Test default behavior of Legistar Site.scrape
    """
    start_date = "2022-04-05"
    end_date = "2022-04-18"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"timezone": "US/Central"}
    site = LegistarSite(url, **config)
    assets = site.scrape(start_date, end_date)
    # 4 agendas and 1 minutes doc
    assert len(assets) == 5
    doc_types = {"agenda": 0, "minutes": 0}
    for asset in assets:
        doc_types[asset.asset_type] += 1
    assert doc_types == {"agenda": 4, "minutes": 1}
    agenda = [
        asset
        for asset in assets
        if asset.url.endswith("M=A&ID=957429&GUID=46C2C864-A1FF-4749-8B19-4915F2A65AF9")
    ][0]
    assert (
        agenda.url
        == "https://nashville.legistar.com/View.ashx?M=A&ID=957429&GUID=46C2C864-A1FF-4749-8B19-4915F2A65AF9"
    )
    assert agenda.committee_name == "Budget and Finance Committee"
    assert agenda.asset_type == "agenda"
    assert agenda.asset_name == "Budget and Finance Committee - 957429 - Agenda"
    assert agenda.meeting_id == "legistar_nashville_957429"
    assert agenda.meeting_date == datetime.datetime(2022, 4, 18, 0, 0)
    # Check time-zone aware meeting time
    expected_dtz = pytz.timezone("US/Central").localize(
        datetime.datetime(2022, 4, 18, 17, 0)
    )
    assert expected_dtz == agenda.meeting_time
    # Content Type and Length are only captured if download flag is True
    assert agenda.content_type is None
    assert agenda.content_length is None


@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@pytest.mark.vcr()
def test_scrape_no_meetings_for_date():
    """
    Scrape should not return assets for dates with no meetings
    """
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"timezone": "US/Central"}
    scrape_date = "2022-01-01"
    site = LegistarSite(url, **config)
    assets = site.scrape(start_date=scrape_date, end_date=scrape_date)
    assert assets == []


@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@pytest.mark.vcr()
def test_scrape_download_default(tmpdir):
    "Scraper should not download file assets by default"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"timezone": "US/Central"}
    scrape_date = "2022-01-01"
    site = LegistarSite(url, **config)
    site.scrape(
        start_date=scrape_date,
        end_date=scrape_date,
    )
    target_dir = tmpdir.join("assets")
    assert not target_dir.exists()


@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@pytest.mark.vcr()
def test_scrape_download_true(tmpdir):
    "Setting download=True should download file assets"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"cache": Cache(tmpdir), "timezone": "US/Central"}
    scrape_date = "2022-04-05"
    site = LegistarSite(url, **config)
    site.scrape(start_date=scrape_date, end_date=scrape_date, download=True)
    target_dir = tmpdir.join("assets")
    actual_files = {f.basename for f in target_dir.listdir()}
    expected = {
        "legistar_nashville_922861_agenda.pdf",
        "legistar_nashville_922861_minutes.pdf",
    }
    assert actual_files == expected


@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@pytest.mark.vcr()
def test_scrape_download_filter_size(tmpdir):
    "Downloads should be filterable by size in MB"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"cache": Cache(tmpdir), "timezone": "US/Central"}
    scrape_date = "2022-04-05"
    site = LegistarSite(url, **config)
    site.scrape(
        start_date=scrape_date, end_date=scrape_date, file_size=0.3, download=True
    )
    # Byte sizes of two files for April 5, 2022
    # Agenda is 453581 bytes
    # Minute is 222117 bytes
    target_dir = tmpdir.join("assets")
    actual_files = [f.basename for f in target_dir.listdir()]
    expected = ["legistar_nashville_922861_minutes.pdf"]
    assert actual_files == expected


@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@pytest.mark.vcr()
def test_scrape_download_filter_type(tmpdir):
    "Downloads should be filterable by type"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"cache": Cache(tmpdir), "timezone": "US/Central"}
    scrape_date = "2022-04-05"
    site = LegistarSite(url, **config)
    site.scrape(
        start_date=scrape_date,
        end_date=scrape_date,
        asset_list=["Agenda"],
        download=True,
    )
    target_dir = tmpdir.join("assets")
    actual_files = [f.basename for f in target_dir.listdir()]
    expected = ["legistar_nashville_922861_agenda.pdf"]
    assert actual_files == expected


@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@patch(
    "civic_scraper.platforms.legistar.site.today_local_str", return_value="2022-04-05"
)
@pytest.mark.vcr()
def test_scrape_current_day_by_default(today_local_str, tmpdir):
    "Scrape should assume current day be default"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"cache": Cache(tmpdir), "timezone": "US/Central"}
    site = LegistarSite(url, **config)
    site.scrape(download=True)
    target_dir = tmpdir.join("assets")
    actual_files = {f.basename for f in target_dir.listdir()}
    expected = {
        "legistar_nashville_922861_agenda.pdf",
        "legistar_nashville_922861_minutes.pdf",
    }
    assert actual_files == expected


@pytest.mark.skip(reason="Known bug in python-lesistar-scraper, Legistar currently not used")
@pytest.mark.vcr()
def test_multiyear_scrape(tmpdir):
    "Downloads should be filterable by size in MB"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = {"cache": Cache(tmpdir), "timezone": "US/Central"}
    # Council meetings on 12/21/21 and 1/4/22 should
    # each yield a pair of Agenda/Minutes
    start_date = "2021-12-21"
    end_date = "2022-01-04"
    site = LegistarSite(url, **config)
    assets = site.scrape(start_date=start_date, end_date=end_date)
    assert len(assets) == 4

import datetime

import pytest
import pytz

from civic_scraper.platforms import LegistarSite


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
    expected_dtz = pytz.timezone('US/Central').localize(datetime.datetime(2022, 4, 18, 17, 0))
    assert expected_dtz == agenda.meeting_time
    # Content Type and Length are only captured if download flag is True
    assert agenda.content_type is None
    assert agenda.content_length is None

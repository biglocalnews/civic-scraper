import datetime
from unittest.mock import patch

import pytest

from civic_scraper.base.cache import Cache
from civic_scraper.platforms import LegistarSite

from .conftest import file_contents


@pytest.mark.vcr()
def test_scrape_defaults():
    """
    Test default behavior of Legistar Site.scrape
    """
    start_date = "2022-04-05"
    end_date = "2022-04-18"
    url = "https://nashville.legistar.com/Calendar.aspx"
    config = { "timezone": "US/Central" }
    site = LegistarSite(url, **config)
    assets = site.scrape(start_date, end_date)
    # 4 agendas and 1 minutes doc
    assert len(assets) == 5
    doc_types = {'agenda': 0, 'minutes': 0}
    for asset in assets:
        doc_types[asset.asset_type] += 1
    assert doc_types == {'agenda': 4, 'minutes': 1}
    agenda = [asset for asset in assets if asset.url.endswith("M=A&ID=957429&GUID=46C2C864-A1FF-4749-8B19-4915F2A65AF9")][0]
    assert (
        agenda.url
        == "https://nashville.legistar.com/View.ashx?M=A&ID=957429&GUID=46C2C864-A1FF-4749-8B19-4915F2A65AF9"
    )
    assert agenda.committee_name == "Budget and Finance Committee"
    assert agenda.asset_type == "agenda"
    assert (
        agenda.asset_name == "Budget and Finance Committee - 957429 - Agenda"
    )
    assert agenda.meeting_id == "legistar_nashville_957429"
    """
    assert agenda.meeting_date == datetime.datetime(2022, 4, 18)
    assert agenda.meeting_time is None
    assert agenda.place == "nashville"
    assert agenda.state_or_province == "tn"
    assert agenda.content_type == "application/pdf"
    assert agenda.content_length == "19536"
    # Check that assets are in the correct date range
    expected_meeting_dates = [datetime.datetime(2020, 5, day) for day in range(3, 7)]
    for asset in assets:
        assert asset.meeting_date in expected_meeting_dates
    """



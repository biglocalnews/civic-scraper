'''
TITLE: test_civicplus.py
AUTHOR: Serdar Tumgoren and Amy DiPierro
VERSION: 2020-09-02
USAGE: pytest -q test_civicplus.py

Tests basic functionality of civicplus.py
'''
# Libraries
import datetime
import pytest
from civic_scraper.scrapers import CivicPlusSite

# Code

@pytest.mark.vcr()
def test_scrape_defaults():
    '''
    Test default behavior of CivicPlus.scrape
    '''
    site_url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    start_date = "2020-05-03"
    end_date = "2020-05-06"
    expected_meeting_dates = [
        datetime.date(2020, 5, day)
        for day in range(3, 7)
    ]
    cp = CivicPlusSite(site_url)
    assets = cp.scrape(start_date, end_date).assets
    # Check asset count
    assert len(assets) == 4
    # Spot check asset attributes.
    # Start simple, and add more attribute
    # checks as needed to cover expected
    # edge cases (or better yet, put those
    # checks in a separate test).
    first = assets[0]
    assert first.url == 'http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05052020-382'
    assert first.committee_name == 'Board of Commissioners 2020'
    assert first.asset_name == 'May 05, 2020, May 5, 2020 Recessed Meeting/Budget Work Session Agenda. Agenda'
    assert first.place == 'nashcounty'
    assert first.state_or_province == 'nc'
    assert first.asset_type == 'agenda'
    assert first.meeting_date == datetime.date(2020, 5, 5)
    assert first.meeting_time == None
    assert first.meeting_id == 'civicplus_nc_nashcounty_05052020-382'
    assert first.scraped_by == 'civicplus.py_1.0.0'
    assert first.content_type == 'application/pdf'
    assert first.content_length == '19536'
    # Check that assets are in the correct date range
    for asset in assets:
        assert asset.meeting_date in expected_meeting_dates
    # Check range of asset types
    expected_asset_types = ['agenda', 'minutes', 'agenda', 'minutes']
    actual_asset_types = [asset.asset_type for asset in assets]
    assert expected_asset_types == actual_asset_types

@pytest.mark.vcr()
def test_scrape_parameters_1():
    '''
    Test behavior of CivicPlus.scrape with lots of parameters
    '''
    site_url = "http://fl-zephyrhills.civicplus.com/AgendaCenter"
    start_date = "2020-08-01"
    end_date = "2020-08-31"
    file_size = 20
    asset_list = ['agenda_packet']
    expected_meeting_dates = [
        datetime.date(2020, 8, day)
        for day in range(1, 32)
    ]
    cp = CivicPlusSite(site_url)
    assets = cp.scrape(start_date=start_date, end_date=end_date, file_size=file_size, asset_list=asset_list).assets
    # Check asset count
    assert len(assets) == 15
    # Spot check asset attributes.
    # Start simple, and add more attribute
    # checks as needed to cover expected
    # edge cases (or better yet, put those
    # checks in a separate test).
    first = assets[0]
    assert first.url == 'http://fl-zephyrhills.civicplus.com/AgendaCenter/ViewFile/Agenda/_08172020-360?html=true'
    assert first.asset_name == 'August 17, 2020, Airport Advisory Regular Meeting. HTML'
    assert first.committee_name == 'Airport Authority 2020'
    assert first.place == 'zephyrhills'
    assert first.state_or_province == 'fl'
    assert first.asset_type == 'agenda'
    assert first.meeting_date == datetime.date(2020, 8, 17)
    assert first.meeting_time == None
    assert first.meeting_id == 'civicplus_fl_zephyrhills_08172020-360'
    assert first.scraped_by == 'civicplus.py_1.0.0'
    assert first.content_type == 'text/html'
    assert first.content_length == '2487'
    # Check that assets are in the correct date range
    for asset in assets:
        assert asset.meeting_date in expected_meeting_dates
    # Check that assets have the correct size
    expected_content_lengths = ['2487', '54515', '54517', '3181', '1266122', '1266093', '4889', '1301997', '1301956', '4117', '1303606', '1303584', '3052', '144582', '144610']
    actual_content_lengths = [asset.content_length for asset in assets]
    assert expected_content_lengths == actual_content_lengths
    # Check range of asset types
    for asset in assets:
        assert asset.asset_type == 'agenda'

@pytest.mark.vcr()
def test_scrape_parameters_2():
    '''
    Test behavior of CivicPlus.scrape when there are no responsive assets to scrape
    '''
    site_url = "http://nm-lascruces.civicplus.com/AgendaCenter"
    start_date = "2020-08-29"
    end_date = "2020-08-29"
    cp = CivicPlusSite(site_url)
    assets = cp.scrape(start_date=start_date, end_date=end_date).assets
    # Check asset count
    assert len(assets) == 0

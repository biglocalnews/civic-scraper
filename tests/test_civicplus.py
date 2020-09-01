'''
USAGE: pytest -q test_civicplus.py
'''
import datetime

import pytest
import os.path
from os import path
from civic_scraper.scrapers import CivicPlusSite


# TODO: Parametrize is handy but the below is quite complex.
# We should simplify at the outset by simply testing that one
# of the returned Asset classes provides the expected values.
# This has added benefits: It serves as a form of documentation
# for the available attributes on Asset, and it makes it much
# easier to tell when a given attribute does not return an expected
# value (as opposed to trying to compare a large string to another
# string).
# As you encounter edge cases, I would create additional tests for
# for those. And if you find that edge-case tests greatly resemble the
# code used for the default case, *then* consider using parametrize
# (but with an eye toward keeping its inputs relatively simple).
# Similarly, start by hard-coding expected values inside of a test,
# and then "promote" those values to more reusable fixtures and/or
# parametrize inputs if they present opportunities for reuse.


# Below are some misc TODOs and additional suggestions, in no particular
# order.

# TODO: Replace all hard-coded user-specific paths with tmp_path and derivations
# thereof.

# TODO: User pytest-vcr to record the first live test and code expectations
# based on those static assets

# TODO: Write pseudo code first to define individual test cases
# e.g. -
# 1) test minimal, default case first (for this case, let's limit to start/end date,
# even though these params are not required)
# 2) test metadata download
# 3) test file download
# test targeted downloads (i.e. specifying one or more file types)
# (I.e. no downloads)
# test csv_export
# test csv append behavior
# etc.
# etc.


# In a separate test, test downloads, although that will
# likely require mocking

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
    # checks in a separat test).
    first = assets[0]
    assert first.url == 'http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05052020-382'
    assert first.asset_name == None
    assert first.committee_name == None
    assert first.place == 'nashcounty'
    assert first.state_or_province == 'nc'
    assert first.asset_type == 'agenda'
    assert first.meeting_date == datetime.date(2020, 5, 5)
    assert first.meeting_time == None
    assert first.meeting_id == 'civicplus_nc_nashcounty_no_data'
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


"""
@pytest.mark.parametrize(
    "start_date,end_date,download,target_dir,file_size,asset_list,csv_export,append,length,printed,meeting_range,path_list", [
        (
                "2020-05-03",
                "2020-05-06",
                True,
                "/Users/amydipierro/GitHub/tmp",
                20,
                ['minutes'],
                "/Users/amydipierro/GitHub/tmp/test.csv",
                False,
                4,
                'AssetCollection(['
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05052020-382, '
                'asset_name: None, committee_name: None, place: nashcounty, '
                'state_or_province: nc,  asset_type: agenda, meeting_date: 2020-05-05, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 19536), '
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Minutes/_05052020-382, '
                'asset_name: None, committee_name: None, place: nashcounty, state_or_province: nc,  '
                'asset_type: minutes, meeting_date: 2020-05-05, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 28998), '
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05042020-381, '
                'asset_name: None, committee_name: None, place: nashcounty, '
                'state_or_province: nc,  asset_type: agenda, meeting_date: 2020-05-04, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 4682030), '
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Minutes/_05042020-381, '
                'asset_name: None, committee_name: None, place: nashcounty, '
                'state_or_province: nc,  asset_type: minutes, meeting_date: 2020-05-04, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 33319158)])',
                ["2020-05-06", "2020-05-05", "2020-05-04", "2020-05-03"],
                ["/Users/amydipierro/GitHub/tmp/nashcounty_nc_minutes_2020-05-04.pdf", "/Users/amydipierro/GitHub/tmp/test.csv", "/Users/amydipierro/GitHub/tmp/nashcounty_nc_minutes_2020-05-05.pdf"]
        ),
        (
                "2020-05-03",
                "2020-05-06",
                True,
                "/Users/amydipierro/GitHub/tmp",
                10,
                ['agenda'],
                "/Users/amydipierro/GitHub/tmp/test2.csv",
                True,
                4,
                'AssetCollection(['
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05052020-382, asset_name: None, committee_name: None, place: nashcounty, '
                'state_or_province: nc,  asset_type: agenda, meeting_date: 2020-05-05, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 19536), '
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Minutes/_05052020-382, asset_name: None, committee_name: None, place: nashcounty, '
                'state_or_province: nc,  asset_type: minutes, meeting_date: 2020-05-05, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 28998), '
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05042020-381, asset_name: None, committee_name: None, place: nashcounty, '
                'state_or_province: nc,  asset_type: agenda, meeting_date: 2020-05-04, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 4682030), '
                'Asset(url: http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Minutes/_05042020-381, asset_name: None, committee_name: None, place: nashcounty, '
                'state_or_province: nc,  asset_type: minutes, meeting_date: 2020-05-04, '
                'meeting_time: None, meeting_id: civicplus_nc_nashcounty_no_data, '
                'scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 33319158)])',
                ["2020-05-06", "2020-05-05", "2020-05-04", "2020-05-03"],
                ["/Users/amydipierro/GitHub/tmp/nashcounty_nc_agenda_2020-05-04.pdf",
                 "/Users/amydipierro/GitHub/tmp/test2.csv",
                 "/Users/amydipierro/GitHub/tmp/nashcounty_nc_agenda_2020-05-05.pdf"]

        ),
    ])
def test_scrape(start_date, end_date, download, target_dir, file_size, asset_list, csv_export, append, length, printed,
                meeting_range, path_list):
    '''Tests the function scrape() in CivicPlus. Indirectly tests download() and to_csv() in AssetCollection.'''
    cp = CivicPlusSite("http://nc-nashcounty.civicplus.com/AgendaCenter")
    asset_collection = cp.scrape(start_date, end_date, download, target_dir, file_size, asset_list, csv_export, append)
    # Check to see that the scraper has correctly ID'd how many assets meet the csv criteria
    assert len(asset_collection) == length
    # Check to see that the scraper has collected the metadata we expect
    assert print(asset_collection) == printed
    # Check that the assets are in the correct date range
    for asset in asset_collection:
        assert asset.meeting_date in meeting_range
    # Check that we've downloaded the files we expect
    for file in path_list:
        assert path.exists(file)
    # Clean up: Delete the files we've created.
    for file in path_list:
        os.remove(file)
"""

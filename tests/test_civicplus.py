'''
USAGE: pytest -q test_civicplus.py
'''

import pytest
import os.path
from os import path
from civic_scraper.scrapers import CivicPlusSite

@pytest.fixture
def cp():
    '''Returns a CivicPlusSite instance with base url http://nc-nashcounty.civicplus.com/AgendaCenter'''
    return CivicPlusSite("http://nc-nashcounty.civicplus.com/AgendaCenter")

def test_init(cp):
    assert cp.url == "http://nc-nashcounty.civicplus.com/AgendaCenter"

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

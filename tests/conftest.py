import csv
import datetime
import os
from pathlib import Path

import pytest

# NOTE: To check if vcrpy/pytest-vcr
# is using cassettes as opposed to making
# live web requests, uncomment below
# and pass pytest caplog fixture to
# a test function. More details here:
#  https://vcrpy.readthedocs.io/en/latest/debugging.html
# import vcr
# import logging
# logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from vcrpy
# vcr_log = logging.getLogger("vcr")
# vcr_log.setLevel(logging.INFO)


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    mod_name = request.module.__name__.split("tests.")[-1]
    return os.path.join("tests/cassettes", mod_name)


@pytest.fixture
def civic_scraper_dir(tmp_path):
    return str(tmp_path.joinpath(".civic-scraper"))


@pytest.fixture
def create_scraper_dir(civic_scraper_dir):
    Path(civic_scraper_dir).mkdir(parents=True, exist_ok=True)


@pytest.fixture
def set_default_env(civic_scraper_dir, monkeypatch):
    monkeypatch.setenv("CIVIC_SCRAPER_DIR", civic_scraper_dir)


def path_to_test_dir_file(file_name):
    return str(Path(__file__).parent.joinpath(file_name))


def read_fixture(file_name):
    path = str(Path(__file__).parent.joinpath("fixtures").joinpath(file_name))
    return file_contents(path)


def file_contents(pth):
    with open(pth) as f:
        return f.read()


def file_lines(pth):
    with open(pth) as f:
        return [line.strip() for line in f.readlines()]


def list_dir(pth):
    return [str(p) for p in Path(pth).glob("*")]


def csv_rows(pth):
    with open(pth) as source:
        return [row for row in csv.DictReader(source)]


@pytest.fixture(scope="session")
def search_results_html():
    return read_fixture("civplus_agenda_search_results_page.html")


@pytest.fixture
def one_site_url():
    return ["http://nc-nashcounty.civicplus.com/AgendaCenter"]


@pytest.fixture
def two_site_urls():
    return [
        "http://nc-nashcounty.civicplus.com/AgendaCenter",
        "https://nm-lascruces.civicplus.com/AgendaCenter",
    ]


@pytest.fixture
def asset_inputs():
    return [
        {
            "asset_name": "May 4, 2020 Regular Meeting Agenda",
            "asset_type": "minutes",
            "committee_name": "Board of Commissioners",
            "content_length": "33319158",
            "content_type": "application/pdf",
            "meeting_date": datetime.datetime(2020, 5, 4, 0, 0),
            "meeting_id": "civicplus_nc-nashcounty_05042020-381",
            "meeting_time": None,
            "place": "nashcounty",
            "place_name": "Nash County",
            "scraped_by": "civic-scraper_0.1.0",
            "state_or_province": "nc",
            "url": "http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Minutes/_05042020-381",
        },
        {
            "asset_name": "May 4, 2020 Regular Meeting Agenda",
            "asset_type": "agenda",
            "committee_name": "Board of Commissioners",
            "content_length": "4682030",
            "content_type": "application/pdf",
            "meeting_date": datetime.datetime(2020, 5, 4, 0, 0),
            "meeting_id": "civicplus_nc-nashcounty_05042020-381",
            "meeting_time": None,
            "place": "nashcounty",
            "place_name": "Nash County",
            "scraped_by": "civic-scraper_0.1.0",
            "state_or_province": "nc",
            "url": "http://nc-nashcounty.civicplus.com/AgendaCenter/ViewFile/Agenda/_05042020-381",
        },
    ]

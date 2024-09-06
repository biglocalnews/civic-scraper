from datetime import datetime

from .conftest import read_fixture

from civic_scraper.platforms.civic_plus.parser import Parser


def test_parse_all(search_results_html):
    "Parser should extract all items on page"
    parser = Parser(search_results_html)
    data = parser.parse()
    assert len(data) == 88
    first = data[0]
    assert first["committee_name"] == "Airport Advisory Board"
    assert first["url_path"] == "/AgendaCenter/ViewFile/Agenda/_11192020-808?html=true"
    assert first["meeting_date"] == datetime(2020, 11, 19)
    assert first["meeting_time"] is None
    assert (
        first["meeting_title"]
        == "Airport Advisory Board Meeting Agenda for November 19, 2020"
    )
    assert first["meeting_id"] == "_11192020-808"
    assert first["asset_type"] == "agenda"


def test_extract_all_asset_types_for_meeting(search_results_html):
    parser = Parser(search_results_html)
    data = parser.parse()
    subset = [
        row
        for row in data
        if row["committee_name"] == "Capital Improvements Advisory Committee"
    ]
    assert len(subset) == 4
    asset_types = [row["asset_type"] for row in subset]
    expected_types = [
        "minutes",
        "agenda",
        "agenda",
        "agenda_packet",
    ]
    assert asset_types == expected_types


def test_parse_alameda():
    "Parser should extract all items on page for Alameda WD, which uses a different page structure"
    html = read_fixture("civplus_alameda_water.html")
    parser = Parser(html)
    data = parser.parse()
    assert len(data) == 2
    first = data[0]
    assert first["committee_name"] == "Engineering and Information Technology Committee"
    assert first["url_path"] == "/AgendaCenter/ViewFile/Agenda/_09042024-1447"
    assert first["meeting_date"] == datetime(2024, 9, 4)
    assert first["meeting_time"] is None
    assert first["meeting_title"] == "Agenda"
    assert first["meeting_id"] == "_09042024-1447"
    assert first["asset_type"] == "agenda"

"""
Tests for Digital TownPath utility functions.

Run with: pipenv run pytest -sv tests/test_dtp_scraper_utils.py
"""

import datetime

import pytest
from bs4 import BeautifulSoup

from civic_scraper.platforms.dtp_scraper import utils


# --- Pure function tests (no HTTP) ---


class TestExtractDetailIdFromUrl:
    def test_basic(self):
        url = "https://finetownny.gov/meetings/detail/30"
        assert utils.extract_detail_id_from_url(url) == "30"

    def test_trailing_slash(self):
        url = "https://finetownny.gov/meetings/detail/30/"
        assert utils.extract_detail_id_from_url(url) == "30"

    def test_large_id(self):
        url = "https://finetownny.gov/meetings/detail/9999"
        assert utils.extract_detail_id_from_url(url) == "9999"


class TestParseMeetingDatetime:
    def test_date_string_and_time(self):
        result = utils.parse_meeting_datetime("2026-02-11", "6:30 pm")
        assert result == datetime.datetime(2026, 2, 11, 18, 30)

    def test_date_object_and_time(self):
        date_obj = datetime.date(2026, 2, 11)
        result = utils.parse_meeting_datetime(date_obj, "6:30 pm")
        assert result == datetime.datetime(2026, 2, 11, 18, 30)

    def test_no_time(self):
        result = utils.parse_meeting_datetime("2026-02-11", None)
        assert result == datetime.datetime(2026, 2, 11, 0, 0)

    def test_time_without_space(self):
        result = utils.parse_meeting_datetime("2026-02-11", "6:30pm")
        assert result == datetime.datetime(2026, 2, 11, 18, 30)

    def test_am_time(self):
        result = utils.parse_meeting_datetime("2026-02-11", "10:00 am")
        assert result == datetime.datetime(2026, 2, 11, 10, 0)

    def test_invalid_date_string(self):
        result = utils.parse_meeting_datetime("not-a-date", "6:30 pm")
        assert result is None

    def test_invalid_time_string(self):
        result = utils.parse_meeting_datetime("2026-02-11", "not-a-time")
        # Falls back to midnight
        assert result == datetime.datetime(2026, 2, 11, 0, 0)

    def test_empty_time_string(self):
        result = utils.parse_meeting_datetime("2026-02-11", "")
        assert result == datetime.datetime(2026, 2, 11, 0, 0)


class TestExtractDocuments:
    def test_agenda_only(self):
        html = """
        <div>
            <h3 class="dtp-meeting-agenda">Agenda</h3>
            <a href="https://example.com/agenda.pdf">Agenda PDF</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        docs = utils._extract_documents(soup)
        assert len(docs) == 1
        assert docs[0]["type"] == "agenda"
        assert docs[0]["url"] == "https://example.com/agenda.pdf"
        assert docs[0]["name"] == "Agenda PDF"

    def test_minutes_only(self):
        html = """
        <div>
            <h3 class="dtp-meeting-minutes">Minutes</h3>
            <a href="https://example.com/minutes.pdf">Minutes PDF</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        docs = utils._extract_documents(soup)
        assert len(docs) == 1
        assert docs[0]["type"] == "minutes"

    def test_agenda_and_minutes_separate_parents(self):
        """When agenda and minutes are in separate parent elements, no duplicates."""
        html = """
        <div>
            <div>
                <h3 class="dtp-meeting-agenda">Agenda</h3>
                <a href="https://example.com/agenda.pdf">Agenda PDF</a>
            </div>
            <div>
                <h3 class="dtp-meeting-minutes">Minutes</h3>
                <a href="https://example.com/minutes.pdf">Minutes PDF</a>
            </div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        docs = utils._extract_documents(soup)
        assert len(docs) == 2
        types = [d["type"] for d in docs]
        assert "agenda" in types
        assert "minutes" in types

    def test_no_documents(self):
        html = "<div><p>No documents available</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        docs = utils._extract_documents(soup)
        assert docs == []

    def test_ignores_non_pdf_links(self):
        html = """
        <div>
            <h3 class="dtp-meeting-agenda">Agenda</h3>
            <a href="https://example.com/page">Not a PDF</a>
            <a href="https://example.com/agenda.pdf">Agenda PDF</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        docs = utils._extract_documents(soup)
        assert len(docs) == 1
        assert docs[0]["url"].endswith(".pdf")

    def test_multiple_agendas(self):
        html = """
        <div>
            <h3 class="dtp-meeting-agenda">Agenda</h3>
            <a href="https://example.com/agenda1.pdf">Agenda 1</a>
            <a href="https://example.com/agenda2.pdf">Agenda 2</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        docs = utils._extract_documents(soup)
        assert len(docs) == 2
        assert all(d["type"] == "agenda" for d in docs)

    def test_shared_parent_causes_duplicates(self):
        """Documents: when agenda and minutes share the same parent, links get double-counted.

        This test documents the current behavior. If _extract_documents is
        refactored to fix this, update this test accordingly.
        """
        html = """
        <div>
            <h3 class="dtp-meeting-agenda">Agenda</h3>
            <a href="https://example.com/doc.pdf">Board Packet</a>
            <h3 class="dtp-meeting-minutes">Minutes</h3>
            <a href="https://example.com/minutes.pdf">Minutes PDF</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        docs = utils._extract_documents(soup)
        # Both sections share <div> as parent, so find_parent() returns
        # the same element for both. All PDF links get counted in each section.
        # This is the current (buggy) behavior — more docs than expected
        assert len(docs) > 2


# --- VCR-based tests (use recorded HTTP cassettes) ---


@pytest.mark.vcr()
def test_get_categories():
    categories = utils.get_categories("https://finetownny.gov")
    assert len(categories) == 4
    for cat in categories:
        assert "name" in cat
        assert "url" in cat
        assert cat["name"]  # not empty
        assert cat["url"]  # not empty


@pytest.mark.vcr()
def test_get_meetings_for_category_year():
    url = "https://finetownny.gov/meetings/meetings/Town%20Board/2026"
    meetings, soup = utils.get_meetings_for_category_year(url)
    assert len(meetings) > 0
    for meeting in meetings:
        assert "title" in meeting
        assert "url" in meeting
        assert "detail_id" in meeting
        assert meeting["detail_id"].isdigit()
    # soup is returned for reuse by get_other_years_from_soup
    assert soup is not None


@pytest.mark.vcr()
def test_get_other_years_from_soup():
    # First fetch the page to get the soup (reuses the same cassette as meetings test)
    url = "https://finetownny.gov/meetings/meetings/Town%20Board/2026"
    _meetings, soup = utils.get_meetings_for_category_year(url)
    # Now extract other years from the already-fetched soup
    years = utils.get_other_years_from_soup(soup)
    # Should have at least one other year
    assert len(years) > 0
    for year_info in years:
        assert "year" in year_info
        assert "url" in year_info
        assert year_info["year"].isdigit()


@pytest.mark.vcr()
def test_get_meeting_details():
    details = utils.get_meeting_details("https://finetownny.gov/meetings/detail/30")
    assert details["committee_name"] is not None
    assert details["meeting_title"] is not None
    assert details["meeting_date"] is not None
    assert isinstance(details["meeting_date"], datetime.date)
    assert details["meeting_time"] is not None
    assert isinstance(details["documents"], list)


@pytest.mark.vcr()
def test_get_meeting_details_with_documents():
    """Test a meeting detail page that has document links."""
    details = utils.get_meeting_details("https://finetownny.gov/meetings/detail/29")
    assert details["committee_name"] is not None
    assert len(details["documents"]) > 0
    for doc in details["documents"]:
        assert doc["type"] in ("agenda", "minutes")
        assert doc["url"].endswith(".pdf")

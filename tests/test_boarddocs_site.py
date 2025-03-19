import pytest

from civic_scraper.platforms.boarddocs.site import BoardDocsSite


@pytest.mark.vcr()
def test_get_committee_id():
    """
    Test getting committee ID from BoardDocs site
    """
    url = "https://go.boarddocs.com/pa/stco/Board.nsf"
    site = BoardDocsSite(url)

    committee_id = site._get_committee_id()
    assert committee_id is not None
    assert isinstance(committee_id, str)
    assert len(committee_id) > 0


def test_parse_url():
    """
    Test parsing the BoardDocs URL for state/province and place
    """
    site_url = "https://go.boarddocs.com/pa/stco/Board.nsf"
    site = BoardDocsSite(site_url)
    # Verify URL parsing functionality
    assert site.place == "stco"
    assert site.state_or_province == "pa"

    # Test with different URL
    other_url = "https://go.boarddocs.com/ca/sfusd/Board.nsf"
    other_site = BoardDocsSite(other_url)
    assert other_site.place == "sfusd"
    assert other_site.state_or_province == "ca"


def test_site_initialization():
    """
    Test basic initialization of the BoardDocsSite class
    """
    url = "https://go.boarddocs.com/pa/stco/Board.nsf"
    site = BoardDocsSite(url)

    # Check that essential attributes are set
    assert site.url == url
    assert hasattr(site, 'session')
    assert hasattr(site, 'headers')

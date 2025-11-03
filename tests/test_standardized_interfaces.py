"""
Tests to validate standardized interfaces across all platforms.
"""
import pytest
from unittest.mock import patch, MagicMock

from civic_scraper.base.cache import Cache
from civic_scraper.platforms import CivicPlusSite, GranicusSite, BoardDocsSite, LegistarSite
from civic_scraper.base.constants import ASSET_TYPES


class TestStandardizedInitParameters:
    """Test that all platforms accept the same constructor parameters."""

    def test_url_parameter(self):
        """All platforms should accept a url parameter."""
        url = "https://example.com"
        
        # Create instances of each platform
        civic_plus = CivicPlusSite(url)
        granicus = GranicusSite(url)
        board_docs = BoardDocsSite(url)
        legistar = LegistarSite(url)
        
        # Verify url is set correctly
        assert civic_plus.url == url
        assert granicus.url == url
        assert board_docs.url == url
        assert legistar.url == url

    def test_place_parameter(self):
        """All platforms should accept a place parameter."""
        url = "https://example.com"
        place = "testcity"
        
        # Create instances of each platform
        civic_plus = CivicPlusSite(url, place=place)
        granicus = GranicusSite(url, place=place)
        board_docs = BoardDocsSite(url, place=place)
        legistar = LegistarSite(url, place=place)
        
        # Verify place is set correctly
        assert civic_plus.place == place
        assert granicus.place == place
        assert board_docs.place == place
        assert legistar.place == place

    def test_state_or_province_parameter(self):
        """All platforms should accept a state_or_province parameter."""
        url = "https://example.com"
        state = "ca"
        
        # Create instances of each platform
        civic_plus = CivicPlusSite(url, state_or_province=state)
        granicus = GranicusSite(url, state_or_province=state)
        board_docs = BoardDocsSite(url, state_or_province=state)
        legistar = LegistarSite(url, state_or_province=state)
        
        # Verify state_or_province is set correctly
        assert civic_plus.state_or_province == state
        assert granicus.state_or_province == state
        assert board_docs.state_or_province == state
        assert legistar.state_or_province == state

    def test_cache_parameter(self):
        """All platforms should accept a cache parameter."""
        url = "https://example.com"
        cache = Cache()
        
        # Create instances of each platform
        civic_plus = CivicPlusSite(url, cache=cache)
        granicus = GranicusSite(url, cache=cache)
        board_docs = BoardDocsSite(url, cache=cache)
        legistar = LegistarSite(url, cache=cache)
        
        # Verify cache is set correctly
        assert civic_plus.cache is cache
        assert granicus.cache is cache
        assert board_docs.cache is cache
        assert legistar.cache is cache

    def test_timezone_parameter(self):
        """All platforms should accept a timezone parameter."""
        url = "https://example.com"
        timezone = "US/Pacific"
        
        # Create instances of each platform
        civic_plus = CivicPlusSite(url, timezone=timezone)
        granicus = GranicusSite(url, timezone=timezone)
        board_docs = BoardDocsSite(url, timezone=timezone)
        legistar = LegistarSite(url, timezone=timezone)
        
        # Verify timezone is set correctly (when applicable)
        # Note: Not all platforms may use the timezone parameter
        # so we don't assert in those cases
        assert hasattr(legistar, "timezone")
        if hasattr(legistar, "timezone"):
            assert legistar.timezone == timezone


class TestStandardizedScrapeParameters:
    """Test that all platforms accept the same scrape method parameters."""

    @patch("requests.head")
    @patch("civic_scraper.platforms.civic_plus.site.Parser")
    @patch.object(CivicPlusSite, "_search")
    def test_civicplus_scrape_parameters(self, mock_search, mock_parser_cls, mock_requests_head):
        """CivicPlusSite should accept all standardized scrape parameters."""
        url = "https://example.com"
        site = CivicPlusSite(url)
        
        # Mock the required return values
        mock_search.return_value = ("mock_url", "mock_html")
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_parser_cls.return_value = mock_parser_instance
        
        # Mock the HTTP head request
        mock_head_response = MagicMock()
        mock_head_response.headers = {
            "content-type": "application/pdf",
            "content-length": "1000"
        }
        mock_requests_head.return_value = mock_head_response
        
        # Call scrape with all standardized parameters
        site.scrape(
            start_date="2023-01-01",
            end_date="2023-01-31",
            download=False,
            cache=True,
            file_size=10.5,
            asset_list=["agenda", "minutes"]
        )
        
        # No assertion needed; if the method call doesn't raise an exception, the test passes

    @patch("requests.head")
    @patch("feedparser.parse")
    @patch("requests.get")
    def test_granicus_scrape_parameters(self, mock_get, mock_parser, mock_requests_head):
        """GranicusSite should accept all standardized scrape parameters."""
        url = "https://example.com"
        site = GranicusSite(url)
        
        # Mock the required return values
        mock_response = MagicMock()
        mock_response.text = "<rss></rss>"
        mock_get.return_value = mock_response
        
        mock_parser.return_value = {"entries": []}
        
        # Mock the HTTP head request
        mock_head_response = MagicMock()
        mock_head_response.headers = {
            "content-type": "application/pdf",
            "content-length": "1000"
        }
        mock_requests_head.return_value = mock_head_response
        
        # Call scrape with all standardized parameters
        site.scrape(
            start_date="2023-01-01",
            end_date="2023-01-31",
            download=False,
            cache=True,
            file_size=10.5,
            asset_list=["agenda", "minutes"]
        )
        
        # No assertion needed; if the method call doesn't raise an exception, the test passes

    @patch.object(BoardDocsSite, "get_meetings")
    def test_boarddocs_scrape_parameters(self, mock_get_meetings):
        """BoardDocsSite should accept all standardized scrape parameters."""
        url = "https://example.com"
        site = BoardDocsSite(url)
        
        # Mock the required return values
        mock_get_meetings.return_value = []
        
        # Call scrape with all standardized parameters
        site.scrape(
            start_date="2023-01-01",
            end_date="2023-01-31",
            download=False,
            cache=True,
            file_size=10.5,
            asset_list=["agenda", "minutes"]
        )
        
        # Verify the method was called with the correct parameters
        mock_get_meetings.assert_called_once_with(start_date="2023-01-01", end_date="2023-01-31")

    @patch("requests.head")
    @patch("legistar.events.LegistarEventsScraper")
    def test_legistar_scrape_parameters(self, mock_scraper_cls, mock_requests_head):
        """LegistarSite should accept all standardized scrape parameters."""
        url = "https://example.com"
        site = LegistarSite(url)
        
        # Mock the LegistarEventsScraper
        mock_scraper = MagicMock()
        mock_scraper.events.return_value = [(
            {"Name": "Test Event", 
             "EventDate": "2023-01-15", 
             "EventTime": "10:00 AM",
             "Meeting Details": {"url": "https://example.com?ID=123"}
            },
            {}
        )]
        mock_scraper_cls.return_value = mock_scraper
        
        # Mock the HTTP head request
        mock_head_response = MagicMock()
        mock_head_response.headers = {
            "content-type": "application/pdf",
            "content-length": "1000"
        }
        mock_requests_head.return_value = mock_head_response
        
        # Call scrape with all standardized parameters
        site.scrape(
            start_date="2023-01-01",
            end_date="2023-01-31",
            download=False,
            cache=True,
            file_size=10.5,
            asset_list=["agenda", "minutes"]
        )
        
        # No assertion needed; if the method call doesn't raise an exception, the test passes


class TestStandardizedAssetTypes:
    """Test that platforms use standardized asset types."""
    
    def test_asset_types_constants_exist(self):
        """Verify that ASSET_TYPES constants exist."""
        assert isinstance(ASSET_TYPES, list)
        assert len(ASSET_TYPES) > 0
        assert "agenda" in ASSET_TYPES
        assert "minutes" in ASSET_TYPES
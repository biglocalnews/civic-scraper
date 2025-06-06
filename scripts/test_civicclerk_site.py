import pytest
from civic_scraper.platforms.civic_clerk.site import CivicClerkSite, extract_place_and_state_from_url
from civic_scraper.base.asset import AssetCollection, Asset
import json
import os

@pytest.fixture
def islamorada_api_response():
    # Load the provided JSON fixture from disk
    fixture_path = r".\civic-scraper\tests\fixtures\scraped_events_api_Islamorada_fl.json"
    with open(fixture_path, encoding='utf-8') as f:
        data = json.load(f)
    # Remove empty/invalid event dicts (some trailing objects are empty)
    return [event for event in data if event.get('meeting_id')]

class DummyCivicClerkSite(CivicClerkSite):
    def fetch_all_events(self, start_date=None, end_date=None):
        # Override to return fixture data instead of making real API calls
        return self._test_events

def test_extract_place_and_state_from_url():
    cases = [
        ("https://turlockca.portal.civicclerk.com", ("turlock", "ca")),
        ("https://jacksonmi.civicclerk.com", ("jackson", "mi")),
        ("https://alpharettaga.civicclerk.com", ("alpharetta", "ga")),
        ("https://islamoradafl.portal.civicclerk.com/", ("islamorada", "fl")),
    ]
    for url, expected in cases:
        assert extract_place_and_state_from_url(url) == expected

def test_scrape_returns_assetcollection(islamorada_api_response):
    site = DummyCivicClerkSite(
        url="https://islamoradafl.portal.civicclerk.com/"
    )
    # Convert the fixture format to the API format expected by extract_event_details
    # (simulate the API's publishedFiles -> assets mapping)
    api_events = []
    for event in islamorada_api_response:
        api_event = {
            "id": str(event["meeting_id"]),
            "eventName": event["meeting_name"],
            "startDateTime": event["meeting_date"],
            "eventCategoryName": event["asset_type"],
            "publishedFiles": event.get("assets", [])
        }
        api_events.append(api_event)
    site._test_events = api_events
    assets = site.scrape()
    assert isinstance(assets, AssetCollection)
    # Count total assets in the fixture
    expected_asset_count = sum(len(event.get("assets", [])) for event in islamorada_api_response)
    assert len(assets) == expected_asset_count


def test_scrape_empty():
    site = DummyCivicClerkSite(
        url="https://islamoradafl.portal.civicclerk.com/"
    )
    site._test_events = []
    assets = site.scrape()
    assert isinstance(assets, AssetCollection)
    assert len(assets) == 0


def test_asset_url_and_meeting_url_methods():
    site = CivicClerkSite(url="https://islamoradafl.portal.civicclerk.com/")
    asset_url = site.standardise_asset_url("12345", 99)
    meeting_url = site.standardise_meeting_url("12345")
    assert asset_url.endswith("/event/12345/files/agenda/99")
    assert meeting_url.endswith("/event/12345/overview")

def test_fetch_and_scrape_real_data():
    """
    Integration test: Fetch real data from the actual CivicClerk API and display first 5 assets (with key info).
    This test will make a real HTTP request. Use with caution (may fail if API changes).
    """
    site = CivicClerkSite(
        url="https://islamoradafl.portal.civicclerk.com/"
    )
    assets = site.scrape()
    assert isinstance(assets, AssetCollection)
    print("\nFirst 5 assets scraped:")
    for asset in list(assets)[:5]:
        print(f"Asset Name: {getattr(asset, 'asset_name', None)} | URL: {getattr(asset, 'url', None)} | Meeting Date: {getattr(asset, 'meeting_date', None)}")
    assert len(assets) > 0

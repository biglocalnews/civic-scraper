import os
import json
import logging
from datetime import datetime
from civic_scraper.platforms.onbase.site import OnBaseSite
from civic_scraper.base.cache import Cache
from civic_scraper.base.asset import AssetCollection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test configuration for OnBase site
TEST_URLS = {
    "west_sacramento": {
        "url": "https://meetings.cityofwestsacramento.org/OnBaseAgendaOnline",
        "place": "West Sacramento",
        "state": "CA"
    },
    # Add more OnBase test sites here if needed
}

SELECTED_TEST = "west_sacramento"
start_date = '2025-06-01'
end_date = '2025-07-31'

test_config = TEST_URLS[SELECTED_TEST]
site_url = test_config["url"]
place = test_config["place"]
state = test_config["state"]

print("="*60)
print("TESTING ONBASE SCRAPER")
print("="*60)
print(f"Test Site: {SELECTED_TEST.upper()}")
print(f"Site URL: {site_url}")
print(f"Place: {place}, {state}")
print("-"*60)

site = OnBaseSite(site_url, cache=Cache('/tmp/cache'), place=place, state_or_province=state)

print("Starting scrape...")
assets: AssetCollection = site.scrape(start_date=start_date, end_date=end_date)
print("-"*60)

# Save assets to JSON
output_filename = f"{place.lower().replace(' ', '_')}_{state.lower()}_assets_{datetime.now().strftime('%Y-%m-%d')}.json"
assets_list = [asset.__dict__ for asset in assets]
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(assets_list, f, indent=2, default=str)

print(f"SCRAPING COMPLETE - Found {len(assets)} total assets")
print("="*60)

# Group assets by committee
assets_by_comm = {}
for asset in assets:
    comm = asset.committee_name
    assets_by_comm.setdefault(comm, []).append(asset)

print("ASSETS BY COMMITTEE:")
for comm, items in assets_by_comm.items():
    print(f"\n{comm}: {len(items)} assets")
    for a in items[:3]:
        print(f"  - {a.asset_name} ({a.meeting_date})")
    if len(items) > 3:
        print(f"  ... and {len(items)-3} more")

print("\n" + "="*60)
print("DETAILED ASSET INFORMATION:")
print("="*60)
print(f"SUMMARY: Found {len(assets)} total assets across {len(assets_by_comm)} committees")

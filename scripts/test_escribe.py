import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from civic_scraper.platforms.escribe.site import EscribeSite
from civic_scraper.base.cache import Cache
from civic_scraper.base.asset import AssetCollection

# Configure logging to see scraper details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test URLs for EscribeSite class
TEST_URLS = {
    "site1": {
        "url": "https://pub-knightdalenc.escribemeetings.com/",
        "panel": ["Board of Adjustment"]
    },
    "site2": {
        "url": "https://pub-perry.escribemeetings.com/",
        "panel": ["Council Meeting", "Pre Council"]
    },
    "site3": {
        "url": "https://pub-arroyogrande.escribemeetings.com/",
        "panel": ["City Council Meeting", "Planning Commission Meeting"]
    },
    "site4": {
        "url": "https://pub-horrycountyschools.escribemeetings.com/",
        "panel": ["Board Meeting"]
    }
}

############################################################################

# Select which test to run
SELECTED_TEST = "site1"         # Options: site1, site2, site3, site4

# Define the date range for scraping
start_date='2024-11-01'
end_date='2025-12-31'

############################################################################
test_config = TEST_URLS[SELECTED_TEST]
site_url = test_config["url"]
committees = test_config["panel"]

# Derive place and state for context
if "knightdalenc" in site_url:
    place, state = "Knightdale", "NC"
elif "perry" in site_url:
    place, state = "Perry", "GA"
elif "arroyogrande" in site_url:
    place, state = "Arroyo Grande", "CA"
elif "horrycountyschools" in site_url:
    place, state = "Horry County Schools", "SC"
else:
    place, state = "Unknown", "Unknown"

# Execute single site test
print("="*60)
print("TESTING ESCRIBE SCRAPER")
print("="*60)
print(f"Test Site: {SELECTED_TEST.upper()}")
print(f"Site URL: {site_url}")
print(f"Place: {place}, {state}")
print(f"Committees to scrape: {committees}")
print("-"*60)

site = EscribeSite(site_url, cache=Cache('/tmp/cache'), place=place, state_or_province=state, committee_names=committees)

print("Starting scrape...")
assets: AssetCollection = site.scrape(start_date=start_date, end_date=end_date)
print("-"*60)

# Save assets to JSON
output_filename = f"{place.lower().replace(' ', '_')}_{state.lower()}_{SELECTED_TEST}_assets_{datetime.now().strftime('%Y-%m-%d')}.json"
assets_list = [asset.__dict__ for asset in assets]
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(assets_list, f, indent=2, default=str)

print(f"SCRAPING COMPLETE - Found {len(assets)} total assets")
print("="*60)

# Group assets by committee to check for separation
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

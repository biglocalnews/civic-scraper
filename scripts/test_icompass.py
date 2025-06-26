# load libraries for icompass-specific test
from typing import Dict, List, Optional
import json, os, logging
from dataclasses import dataclass
from civic_scraper.platforms import ICompassSite
from civic_scraper.base.cache import Cache
from civic_scraper.base.asset import AssetCollection
from datetime import datetime

# Configure logging to see scraper detection details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test URLs for each iCompass site
TEST_URLS = {
    "site1": {
        "url": "https://achdidaho.civicweb.net/Portal/MeetingTypeList.aspx",
        "committee": ["Commission Meeting", "Quorum Notice"]
    },
    "site2": {
        "url": "https://newtonkansas.civicweb.net/Portal/MeetingTypeList.aspx",
        "committee": ["Regular Commission", "Aviation Commission"]
    },
    "site3": {
        "url": "https://harveycounty.civicweb.net/Portal/MeetingTypeList.aspx",
        "committee": ["Parks Advisory Board"]
    },
    "site4": {
        "url": "https://derby.civicweb.net/Portal/MeetingTypeList.aspx",
        "committee": ["City Council", "Planning Commission"]
    }
}

# Select which test to run
SELECTED_TEST = "site2"  # Options: site1, site2, site3, site4

test_config = TEST_URLS[SELECTED_TEST]
site_url = test_config["url"]
committees = test_config["committee"]

# Extract site details for configuration
if "achdidaho" in site_url:
    place, state = "Ada County Highway District", "ID"
elif "newtonkansas" in site_url:
    place, state = "Newton", "KS"
elif "harveycounty" in site_url:
    place, state = "Harvey County", "KS"
elif "derby" in site_url:
    place, state = "Derby", "KS"
else:
    place, state = "Unknown", "Unknown"

print("="*60)
print("TESTING ICOMPASS SCRAPER WITH HTML STRUCTURE DETECTION")
print("="*60)
print(f"Test Site: {SELECTED_TEST.upper()}")
print(f"Site URL: {site_url}")
print(f"Place: {place}, {state}")
print(f"Committees to scrape: {committees}")
print("-"*60)

site = ICompassSite(site_url, cache=Cache('/tmp/cache'), place=place, state_or_province=state, committee_names=committees)

print("Starting scrape...")
assets: AssetCollection = site.scrape(start_date = '2025-01-01')
print("-"*60)

# Save assets to JSON
output_filename = f"{place.lower().replace(' ', '_')}_{state.lower()}_{SELECTED_TEST}_assets_{datetime.now().strftime('%Y-%m-%d')}.json"
assets_list = [asset.__dict__ for asset in assets]
with open(output_filename, 'w') as f:
    json.dump(assets_list, f, indent=2, default=str)

print(f"SCRAPING COMPLETE - Found {len(assets)} total assets")
print("="*60)

# Group assets by committee to check for cross-contamination
assets_by_committee = {}
for asset in assets:
    committee = asset.committee_name
    if committee not in assets_by_committee:
        assets_by_committee[committee] = []
    assets_by_committee[committee].append(asset)

print("ASSETS BY COMMITTEE:")
for committee, committee_assets in assets_by_committee.items():
    print(f"\n{committee}: {len(committee_assets)} assets")
    for asset in committee_assets[:3]:
        print(f"  - {asset.asset_name} ({asset.meeting_date})")
    if len(committee_assets) > 3:
        print(f"  ... and {len(committee_assets) - 3} more")

print("\n" + "="*60)
print("DETAILED ASSET INFORMATION:")
print("="*60)

print(f"SUMMARY: Found {len(assets)} total assets across {len(assets_by_committee)} committees")

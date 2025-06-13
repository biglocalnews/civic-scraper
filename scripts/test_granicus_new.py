# load libraries for granicus-specific test
from typing import Dict, List, Optional
import json, os, logging
from dataclasses import dataclass
from civic_scraper.platforms import CivicPlusSite, LegistarSite, GranicusSite
from civic_scraper.base.cache import Cache
from civic_scraper.base.asset import AssetCollection
from civic_scraper.utils import parse_date
from datetime import datetime

# Configure logging to see scraper detection details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test URLs for each scraper type
TEST_URLS = {
    "type1": {
        "url": "https://cityofbradenton.granicus.com/ViewPublisher.php?view_id=1",
        "panel": ["Planning Commission", "City Council"]
    },
    "type2": {
        "url": "https://marysvilleca.granicus.com/ViewPublisher.php?view_id=1",
        "panel": ["Planning Commission", "City Council", "Levee Commission"]
    },
    "type3": {
        "url": "https://sacramento.granicus.com/viewpublisher.php?view_id=22",
        "panel": ["City Council"]
    },
    "type3_alt": {
        "url": "https://rocklin-ca.granicus.com/ViewPublisher.php?view_id=1",
        "panel": ["Civil Service Board", "Civil Service Commission"]
    },
    "type4": {
        "url": "https://coralsprings.granicus.com/ViewPublisher.php?view_id=3",
        "panel": ["Coral Springs City Commission","Development Review Committee"]
    }
}

# Select which test to run
SELECTED_TEST = "type4"  # Options: type1, type2, type3, type3_alt, type4

# Get the selected test configuration
if SELECTED_TEST not in TEST_URLS:
    raise ValueError(f"Invalid test selection: {SELECTED_TEST}. Available options: {list(TEST_URLS.keys())}")

test_config = TEST_URLS[SELECTED_TEST]
site_url = test_config["url"]
committees = test_config["panel"]

# Extract site details for configuration
if "bradenton" in site_url:
    place, state = "Bradenton", "FL"
elif "marysvilleca" in site_url:
    place, state = "Marysville", "CA"
elif "sacramento" in site_url:
    place, state = "Sacramento", "CA"
elif "rocklin" in site_url:
    place, state = "Rocklin", "CA"
elif "coralsprings" in site_url:
    place, state = "Coral Springs", "FL"
else:
    place, state = "Unknown", "Unknown"

# Execute single site test
print("="*60)
print("TESTING GRANICUS SCRAPER WITH HTML STRUCTURE DETECTION")
print("="*60)
print(f"Test Type: {SELECTED_TEST.upper()}")
print(f"Site URL: {site_url}")
print(f"Place: {place}, {state}")
print(f"Committees to scrape: {committees}")
print("-"*60)

site = GranicusSite(site_url, cache=Cache('/tmp/cache'), place=place, state_or_province=state, committee_names=committees)

print("Starting scrape...")
assets: AssetCollection = site.scrape(start_date = '2025-01-01')
print("-"*60)

# Save assets to JSON
output_filename = f"{place.lower().replace(' ', '_')}_{state.lower()}_{SELECTED_TEST}_assets_{datetime.now().strftime('%Y-%m-%d')}.json"
assets_list = [asset.__dict__ for asset in assets]
with open(output_filename, 'w') as f:
    json.dump(assets_list, f, indent=2, default=str) # Added default=str to handle non-serializable types like datetime

# Examine the results
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
    for asset in committee_assets[:3]:  # Show first 3 assets per committee
        print(f"  - {asset.asset_name} ({asset.meeting_date})")
    if len(committee_assets) > 3:
        print(f"  ... and {len(committee_assets) - 3} more")

print("\n" + "="*60)
print("DETAILED ASSET INFORMATION:")
print("="*60)

  
print(f"SUMMARY: Found {len(assets)} total assets across {len(assets_by_committee)} committees")

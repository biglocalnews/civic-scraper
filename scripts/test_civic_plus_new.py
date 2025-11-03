import sys
import os
from datetime import datetime
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from civic_scraper.platforms.civic_plus.site import Site as CivicPlusSite

# List of CivicPlus sites to test
sites = [
    # Original test site
    "http://nc-nashcounty.civicplus.com/AgendaCenter",
    # New sites provided
    # "https://www.statecollegepa.us/606/Borough-Council-Agendas-Minutes",
    # "https://www.statecollegepa.us/531/Planning-Commission-Agendas-Minutes",
    # "https://twp.patton.pa.us/AgendaCenter/Planning-Commission-6",
    # "https://www.collegetownship.org/AgendaCenter"
]

# Date range for scraping
start_date_str = "2023-01-01"
end_date_str = "2023-12-31" 

# Try each site until we get successful results
for civic_plus_url in sites:
    try:
        print(f"\n===== Testing site: {civic_plus_url} =====")
        
        # Initialize scraper for current URL
        scraper = CivicPlusSite(civic_plus_url)
        
        # Scrape meetings using the scrape function with a date range
        print(f"Scraping meetings from {civic_plus_url}")
        assets = scraper.scrape(start_date=start_date_str, end_date=end_date_str)
        
        # Convert the AssetCollection to a list of dictionaries for JSON output
        output_data = [
            {
                "asset_name": asset.asset_name if hasattr(asset, 'asset_name') else 'Unknown',
                "committee_name": asset.committee_name if hasattr(asset, 'committee_name') else 'Unknown',
                "meeting_date": str(asset.meeting_date) if hasattr(asset, 'meeting_date') else 'Unknown',
                "url": asset.url if hasattr(asset, 'url') else 'Unknown'
            } 
            for asset in assets
        ]
        
        if output_data:
            print(f"Found {len(output_data)} assets!")
            print(json.dumps(output_data[:3], indent=4))  # Show first 3 assets
            
            # Optional: Uncomment to test with cache and download options
            # print("\nTesting with additional options (cache, download)...")
            # assets_with_options = scraper.scrape(
            #     start_date=start_date_str, 
            #     end_date=end_date_str, 
            #     cache=True, 
            #     download=True, 
            #     file_size=10
            # )
            # output_data_with_options = [
            #     {
            #         "asset_name": asset.asset_name if hasattr(asset, 'asset_name') else 'Unknown',
            #         "committee_name": asset.committee_name if hasattr(asset, 'committee_name') else 'Unknown',
            #         "meeting_date": str(asset.meeting_date) if hasattr(asset, 'meeting_date') else 'Unknown',
            #         "url": asset.url if hasattr(asset, 'url') else 'Unknown'
            #     } 
            #     for asset in assets_with_options
            # ]
            # print(f"Found {len(output_data_with_options)} assets with options!")
            # print(json.dumps(output_data_with_options[:3], indent=4))
            
        else:
            print("No assets found for this site. Trying another site...")
            
    except Exception as e:
        print(f"Error testing site {civic_plus_url}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("Trying another site...")
        continue

# If we tried all sites and none worked
else:
    print("\n⚠️ Could not find any meetings from any of the test sites.")
    print("Check the error messages above for more details.")
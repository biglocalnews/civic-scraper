
import json
import logging
import os
import sys

# Add the project root to the Python path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from civic_scraper.platforms.granicus.site import GranicusSite
from civic_scraper.base.cache import Cache

# Configure logging to show detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'test_config_copy.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    sites = config.get('sites', {})
    
    # Initialize cache
    cache = Cache()

    for site_name, site_info in sites.items():
        logging.info(f"--- Testing site: {site_name} ---")
        
        # Extract site information from config
        url = site_info.get('url')
        place = site_info.get('place')
        state = site_info.get('state')
        committee_names = site_info.get('committees')
        start_date = site_info.get('start_date')

        if not url:
            logging.error(f"URL not found for site: {site_name}. Skipping.")
            continue

        try:
            # Initialize GranicusSite with the provided info
            site = GranicusSite(
                url,
                place=place,
                state_or_province=state,
                cache=cache,
                committee_names=committee_names
            )

            # Run the scraper
            assets = site.scrape(start_date=start_date)

            logging.info(f"Found {len(assets)} assets for site: {site_name}")

        except Exception as e:
            logging.error(f"An error occurred while testing site {site_name}: {e}", exc_info=True)
        
        logging.info(f"--- Finished testing site: {site_name} ---\
")

if __name__ == "__main__":
    main()

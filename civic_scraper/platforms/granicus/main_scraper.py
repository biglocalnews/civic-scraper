import logging
import os
import sys
from datetime import datetime  # For testing date filtering if added
from civic_scraper.platforms.granicus.site import GranicusSite
from civic_scraper.base.cache import Cache  # Assuming this is available
from civic_scraper.base.asset import (
    AssetCollection,
    Asset,
)  # For type hinting and inspection
from civic_scraper.platforms.granicus.site import (
    GranicusSite,
)  # Tries to import from current dir
from civic_scraper.base.cache import Cache
from civic_scraper.base.asset import (
    AssetCollection,
    Asset,
)  # For type hinting and inspection


# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO for less verbose default output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_granicus_test_scrape(
    url: str, panel_name: str | None = None, site_name_override: str | None = None
):
    """
    Tests the GranicusSite scraper for a given URL and panel.
    """
    logger.info(f"--- Test: URL: {url}, Panel: {panel_name or 'N/A'} ---")

    test_cache = None
    # Instantiate GranicusSite
    site_instance_name = site_name_override or url.split(".")[0].replace("https://", "")
    granicus_site = GranicusSite(url, cache=test_cache, name=site_instance_name)

    # Call the scrape method
    # Pass committee_name which corresponds to panel_name
    asset_collection: AssetCollection = granicus_site.scrape(committee_name=panel_name)

    if asset_collection and len(asset_collection) > 0:
        logger.info(f"Successfully scraped {len(asset_collection)} assets.")
        logger.info("First few assets:")
        for i, asset in enumerate(asset_collection):
            if i < 3:  # Print details of first 5 assets
                logger.info(
                    f"  Asset {i+1}: Name='{asset.asset_name}', Date='{asset.meeting_date.strftime('%Y-%m-%d')}', "
                    f"Type='{asset.asset_type}', URL='{asset.url}', MeetingID='{asset.meeting_id}', "
                    f"Committee='{asset.committee_name}'"
                )
            else:
                break
    elif asset_collection is not None:  # Empty collection
        logger.info("Scrape completed, but no assets were found or processed.")
    else:  # Should not happen if scrape returns empty AssetCollection on failure/no data
        logger.error(
            "Scrape method returned None, which is unexpected. Expected AssetCollection."
        )

    logger.info(f"--- Test for {url} (Panel: {panel_name}) finished ---")
    return asset_collection


if __name__ == "__main__":
    # Test cases
    test_configurations = [
        # {
        #     "url": "https://cityofbradenton.granicus.com/ViewPublisher.php?view_id=1",
        #     "panel": "City Council",
        #     "comment": "Type 1: Bradenton City Council"
        # },
        # {
        #     "url": "https://marysvilleca.granicus.com/ViewPublisher.php?view_id=1",
        #     "panel": "City Council",
        #     "comment": "Type 2: Marysville City Council"
        # },
        # {
        #     "url": "https://sacramento.granicus.com/ViewPublisher.php?view_id=22",
        #     "panel": "City Council",
        #     "comment": "Type 3: Sacramento (City Council)"
        # },
        # {
        #     "url": "https://rocklin-ca.granicus.com/ViewPublisher.php?view_id=1",
        #     "panel": "Civil Service Commission",
        #     "comment": "Type 3: Rocklin Civil Service Commission"
        # },
        # {
        #     "url": "https://coralsprings.granicus.com/ViewPublisher.php?view_id=3",
        #     "panel": "Coral Springs City Commission",
        #     "comment": "Type 4: Coral Springs City Commission"
        # },
        {
            "url": "https://sibfl.granicus.com/ViewPublisher.php?view_id=2",
            "panel": "City Commission",
            "comment": "SIBFL City Commission (likely Type 3)",
        }
    ]

    # --- To run all tests: ---
    all_results = {}
    for test_case in test_configurations:
        logger.info(f"\n===================================================")
        logger.info(f"RUNNING TEST: {test_case['comment']}")
        assets = run_granicus_test_scrape(test_case["url"], test_case.get("panel"))
        all_results[test_case["comment"]] = assets
        logger.info(f"===================================================\n")

    # --- Example of how to run a single selected test: ---
    # selected_test = test_configurations[0] # Choose a test
    # logger.info(f"\n===================================================")
    # logger.info(f"RUNNING SELECTED TEST: {selected_test['comment']}")
    # run_granicus_test_scrape(selected_test["url"], selected_test.get("panel"))
    # logger.info(f"===================================================\n")

    logger.info("All Granicus scraping tests completed.")

# to run all test: python scripts\test_granicus.py
# terminal command to test how platform handles one url: python scripts\test_granicus.py --type platform --url "https://sacramento.granicus.com/viewpublisher.php?view_id=22" --panel "City Council"
# terminal command to test a specific type: python scripts\test_granicus.py --type 3  --url "https://sacramento.granicus.com/viewpublisher.php?view_id=22" --panel "City Council"

import os
import sys
import logging
import argparse
import json
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Granicus scrapers from the package
try:
    from civic_scraper.platforms.granicus.type1 import GranicusType1Scraper
    from civic_scraper.platforms.granicus.type2 import GranicusType2Scraper
    from civic_scraper.platforms.granicus.type3 import GranicusType3Scraper
    from civic_scraper.platforms.granicus.type4 import GranicusType4Scraper
    from civic_scraper.platforms.granicus.site import GranicusSite
    from civic_scraper.base.asset import AssetCollection
    logger.info("Successfully imported Granicus scrapers")
except ImportError as e:
    logger.error(f"Failed to import Granicus scrapers: {str(e)}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Current sys.path: {sys.path}")
    logger.error("Make sure you're running from the project root or the paths are correct")
    sys.exit(1)

# Test URLs for each scraper type
TEST_URLS = {
    "type1": {
        "url": "https://cityofbradenton.granicus.com/ViewPublisher.php?view_id=1",
        "panel": ["Planning Commission", "City Council"]
    },
    "type2": {
        "url": "https://marysvilleca.granicus.com/ViewPublisher.php?view_id=1",
        "panel": ["Planning Commission", "City Council"]
    },
    "type3": {
        "url": "https://sacramento.granicus.com/viewpublisher.php?view_id=22",
        "panel": ["City Council"]
    },
    "type4": {
        "url": "https://coralsprings.granicus.com/ViewPublisher.php?view_id=3",
        "panel": ["Coral Springs City Commission"]
    }
}

def test_specific_scraper(scraper_type, url, panel_name):
    """
    Test a specific Granicus scraper type with a given URL and panel name.
    
    Args:
        scraper_type: The scraper class to use
        url: The URL to scrape
        panel_name: The name of the panel/committee to scrape
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Testing {scraper_type.__name__} with URL: {url} (Panel: {panel_name})")
    try:
        # Instantiate the scraper
        scraper = scraper_type()

        # Fetch HTML content
        logger.debug(f"Fetching HTML content from {url}")
        html_content = scraper._fetch_html(url)

        if not html_content:
            logger.error(f"Failed to fetch HTML content from {url}")
            return False

        logger.debug(f"Successfully fetched HTML content ({len(html_content)} bytes)")

        # Extract and process meetings using the type scraper directly
        asset_collection = scraper.extract_and_process_meetings(
            html_content=html_content,
            site_url=url,
            site_place=None,
            site_state=None,
            site_committee_name=panel_name,
            site_timezone=None
        )

        if asset_collection and len(asset_collection) > 0:
            logger.info(f"Successfully scraped {len(asset_collection)} assets.")
            logger.info("First few assets:")
            for i, asset in enumerate(asset_collection):
                if i < 5: # Print details of first 5 assets
                    logger.info(
                        f"  Asset {i+1}: Name='{asset.asset_name}', Date='{asset.meeting_date.strftime('%Y-%m-%d')}', "
                        f"Type='{asset.asset_type}', URL='{asset.url}', MeetingID='{asset.meeting_id}', "
                        f"Committee='{asset.committee_name}'"
                    )
                else:
                    break
        elif asset_collection is not None: # Empty collection
            logger.info("Scrape completed, but no assets were found or processed.")
        else: # Should not happen if extract_and_process_meetings returns None
            logger.error("extract_and_process_meetings method returned None, which is unexpected. Expected AssetCollection.")

        logger.info(f"--- Test for {url} (Panel: {panel_name}) finished ---")
        return asset_collection and len(asset_collection) > 0
    except Exception as e:
        logger.error(f"Error testing {scraper_type.__name__}: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def test_scrape_granicus_platform(url, panel_name):
    """
    Test the main scrape_granicus_platform function with a given URL and panel name.
    
    Args:
        url: The URL to scrape
        panel_name: The name of the panel/committee to scrape
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Testing scrape_granicus_platform with URL: {url} (Panel: {panel_name})")
    try:
        # Pass committee_names as a list to GranicusSite
        scraper = GranicusSite(url, committee_names=[panel_name] if panel_name else None)
        
        logger.info(f"Successfully tested scrape_granicus_platform for {url}")
        return scraper.scrape() is not None
    
    except Exception as e:
        logger.error(f"Error testing scrape_granicus_platform: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

def run_all_tests():
    """Run all scraper tests with their specific URLs."""
    results = {}

    # Test each panel for each type scraper
    type_scrapers = [
        ("type1", GranicusType1Scraper),
        ("type2", GranicusType2Scraper),
        ("type3", GranicusType3Scraper),
        ("type4", GranicusType4Scraper),
    ]
    for type_name, scraper_cls in type_scrapers:
        url = TEST_URLS[type_name]["url"]
        panels = TEST_URLS[type_name]["panel"]
        # Run test for each panel individually
        panel_results = []
        for panel in panels:
            result = test_specific_scraper(scraper_cls, url, panel)
            results[f"{type_name}_{panel}"] = result
            panel_results.append(result)
        # Overall type result is True if all panels pass (stricter, but more accurate)
        results[type_name] = all(panel_results)

    # Test the main scrape_granicus_platform function with each URL
    for scraper_type, test_data in TEST_URLS.items():
        # For platform, pass only the first panel (to match previous logic)
        panel = test_data["panel"][0] if isinstance(test_data["panel"], list) else test_data["panel"]
        results[f"platform_{scraper_type}"] = test_scrape_granicus_platform(
            test_data["url"],
            panel
        )

    # Print summary of results
    logger.info("Test Results Summary:")
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"  {test_name}: {status}")

    # Return True if all tests passed
    return all(results.values())

def run_specific_test(scraper_type, url, panel_name=None):
    """
    Run a test for a specific scraper type and URL.
    
    Args:
        scraper_type: The type of scraper to use (1, 2, 3, 4, or 'platform')
        url: The URL to scrape
        panel_name: The name of the panel/committee to scrape
    
    Returns:
        bool: True if successful, False otherwise
    """
    if scraper_type == "platform":
        return test_scrape_granicus_platform(url, panel_name)
    
    scraper_map = {
        "1": GranicusType1Scraper,
        "2": GranicusType2Scraper,
        "3": GranicusType3Scraper,
        "4": GranicusType4Scraper
    }
    
    if scraper_type not in scraper_map:
        logger.error(f"Invalid scraper type: {scraper_type}")
        return False
    
    return test_specific_scraper(scraper_map[scraper_type], url, panel_name)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Granicus scrapers")
    parser.add_argument(
        "--type", 
        choices=["1", "2", "3", "4", "platform", "all"],
        default="all",
        help="Scraper type to test (1-4, platform, or all)"
    )
    parser.add_argument(
        "--url", 
        help="URL to scrape (required if type is not 'all')"
    )
    parser.add_argument(
        "--panel", 
        help="Panel/committee name to scrape"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode with verbose logging"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.type != "all" and not args.url:
        parser.error("--url is required when --type is not 'all'")
    
    return args

if __name__ == "__main__":
    args = parse_arguments()
    
    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Print system information
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Script location: {os.path.abspath(__file__)}")
    
    # Create directories for output if they don't exist
    os.makedirs("scraped_data", exist_ok=True)
    
    try:
        if args.type == "all":
            success = run_all_tests()
        else:
            success = run_specific_test(args.type, args.url, args.panel)
        
        # Exit with appropriate status code
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        if args.debug:
            logger.error(traceback.format_exc())
        sys.exit(1)


from civic_scraper.base.cache import Cache
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.platforms.escribe.site import EscribeSite
import pytest
from dataclasses import dataclass
from typing import List, Optional
import logging
import json
import os


@dataclass
class SiteConfig:
    url: str
    state: str
    place: str
    platform: str
    committees: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def load_test_config():
    """
    Test loading the test_config.json.

    Inputs: None

    Returns:
        None loads the JSON file
    """
    with open("test_config.json") as f:
        config_data = json.load(f)

        return config_data


def test_config_location():
    """
    Ensure that the test_config.json is within the directory.
    """
    assert os.path.exists(
        "test_config.json"
    ), "test_config file does not exist, please use create_test_config.py to create the base config."


def test_single_scrape():
    """
    Assert that a single run of the scraper returns assets.
    """

    # grab the first site from the test config for a focused test
    config = load_test_config()
    test_site = next(iter(config["sites"].values()))

    # define the test site
    site = EscribeSite(
        url=test_site["url"],
        place=test_site["place"],
        state_or_province=test_site["state"],
        cache=Cache("/tmp/cache"),
        committee_names=test_site["committees"],
    )
    assets: AssetCollection = site.scrape(start_date="2025-01-01")

    # NOTE: UNCOMMENT THE CODE BELOW TO LOG ASSET INFORMATION
    # log the assets found and content of the scraper
    # logging.info(f"Found {len(assets)} total assets in test single site\n")
    # for i, asset in enumerate(assets, start=1):
    #     logging.info(f"Asset {i} for {test_site['place']}:")
    #     for key, value in asset.__dict__.items():
    #         logging.info(f"  {key}: {value}")
    #     logging.info("")

    # assert assets is a list of AssetCollection
    assert isinstance(assets, AssetCollection), f"Expected list, got {type(assets)}"
    assert all(
        isinstance(a, Asset) for a in assets
    ), "Not all items are Asset instances"

    # ensure that at least one asset is returned for the test site
    assert len(assets) > 0, f"No assets returned for site: {test_site['place']}"


def test_scraper_returns_assets():
    """
    Ensure scraper returns at least one asset for each site in config with any missing sites logged.
    """
    config = load_test_config()
    total_assets = []
    expected_places = set()

    for site_config in config["sites"]:
        configuration_data = config["sites"][site_config]
        expected_places.add(configuration_data["place"])

        site = EscribeSite(
            url=configuration_data["url"],
            cache=Cache("/tmp/cache"),
            place=configuration_data["place"],
            state_or_province=configuration_data["state"],
            committee_names=configuration_data["committees"],
        )
        assets = site.scrape()
        total_assets.extend(assets)

        logging.info("Running test_scraper_returns_assets")
        logging.info(
            f"Found {len(assets)} total assets for {configuration_data['place']}\n"
        )

        # NOTE: UNCOMMENT THE CODE BELOW TO LOG ASSET INFORMATION
        # loop through the assets within the asset collection and ensure that each asset returns values
        # for i, asset in enumerate(assets, start=1):
        #     logging.info(f"Asset {i} for {configuration_data['place']}:")
        #     for key, value in asset.__dict__.items():
        #         logging.info(f"  {key}: {value}")
        #     logging.info("")

        assert isinstance(
            assets, AssetCollection
        ), f"Expected AssetCollection, got {type(assets)}"
        assert all(
            isinstance(a, Asset) for a in assets
        ), "Not all items are Asset instances"
        assert (
            len(assets) > 0
        ), f"No assets returned for site: {config.get('site_name', 'Unknown')}"

    asset_places = {getattr(asset, "place", None) for asset in total_assets}
    missing_places = expected_places - asset_places

    logging.info(f"The following places returned Assets {asset_places}")
    logging.info(
        f"There are {len(missing_places)} locations from the config missing assets"
    )
    if len(missing_places) != 0:
        logging.info(f"Locations without assets {missing_places}")
    assert (
        not missing_places
    ), f"The following places were in the config but not found in any asset: {missing_places}"


def test_each_committee_returns_assets():
    """
    Ensure scraper returns at least one asset for each site in config,
    with any missing places logged.
    """
    config = load_test_config()

    for site_config in config["sites"]:
        configuration_data = config["sites"][site_config]

        site = EscribeSite(
            url=configuration_data["url"],
            cache=Cache("/tmp/cache"),
            place=configuration_data["place"],
            state_or_province=configuration_data["state"],
            committee_names=configuration_data["committees"],
        )

        assets = site.scrape()

        logging.info(f"Testing committees for site: '{configuration_data['place']}'")
        assert isinstance(
            assets, AssetCollection
        ), f"Expected AssetCollection, got {type(assets)}"

        for committee in configuration_data["committees"]:
            committee_assets = [
                a for a in assets if getattr(a, "committee_name", None) == committee
            ]
            logging.info(
                f"Found {len(committee_assets)} assets for committee '{committee}' in '{configuration_data['place']}'"
            )
            assert (
                committee_assets
            ), f"No assets found for committee '{committee}' in place '{configuration_data['place']}'"


def test_no_assets_returned():
    """
    Ensure that the scraper returns no assets with an invalid JSON configuration
    """
    invalid_site = {
        "state": "NO",
        "place": "Invalid County",
        "platform": "escribe",
        "url": "https://example_invalid_site.com",
        "committees": ["No Committees"],
        "start_date": "2025-01-01",
    }

    site = EscribeSite(
        url=invalid_site["url"],
        place=invalid_site["place"],
        state_or_province=invalid_site["state"],
        cache=Cache("/tmp/cache"),
        committee_names=invalid_site["committees"],
    )

    assets: AssetCollection = site.scrape(start_date="2025-01-01")
    # assert assets is a list of AssetCollection
    assert isinstance(assets, AssetCollection), f"Expected list, got {type(assets)}"
    assert all(
        isinstance(a, Asset) for a in assets
    ), "Not all items are Asset instances"
    # Should fail to fetch meetings


def test_invalid_config():
    """
    Ensure that the scraper does not run and a Type Error is returned due to missing config information.
    """
    config_missing_info = {
        "url": None,
        "committee_name": [None],
        "place": None,
        "state": None,
    }

    with pytest.raises(TypeError) as exc_info:
        scraper = EscribeSite(
            site_config=config_missing_info["url"],
            cache=Cache(),
            place=config_missing_info["place"],
            state_or_province=config_missing_info["state"],
            committee_names=config_missing_info["committee_name"],
        )
        # this line should not run, the TypeError should be raised above during the init
        scraper.scrape()

    assert "__init__()" in str(exc_info.value)
    assert "missing 1 required positional argument" in str(
        exc_info.value
    ) or "got an unexpected keyword argument" in str(exc_info.value)
